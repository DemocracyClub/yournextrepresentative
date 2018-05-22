from __future__ import unicode_literals

from datetime import date
import json
from os.path import join
import re

from django.conf import settings
from django.contrib.admin.utils import NestedObjects
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.db import models
from django.template import loader, Context
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _l
from django.utils.six import text_type
from django.utils.six.moves.urllib_parse import urljoin, quote_plus

from dateutil import parser
from slugify import slugify
from django_date_extensions.fields import ApproximateDate

from elections.models import Election, AreaType
from popolo.models import (
    ContactDetail, Person, Organization, Post, Membership, Area, Identifier
)
from images.models import Image, HasImageMixin

from compat import python_2_unicode_compatible
from .fields import (
    ExtraField, PersonExtraFieldValue, ComplexPopoloField,
    get_complex_popolo_fields,
)
from ..diffs import get_version_diffs
from ..twitter_api import update_twitter_user_id, TwitterAPITokenMissing
from .versions import get_person_as_version_data

"""Extensions to the base django-popolo classes for YourNextRepresentative

These are done via explicit one-to-one fields to avoid the performance
problems with multi-table inheritance; it's preferable to state when you
want a join or not.

  http://stackoverflow.com/q/23466577/223092

"""


def update_person_from_form(person, person_extra, form):
    form_data = form.cleaned_data.copy()
    # The date is returned as a datetime.date, so if that's set, turn
    # it into a string:
    birth_date_date = form_data['birth_date']
    if birth_date_date:
        form_data['birth_date'] = repr(birth_date_date).replace("-00-00", "")
    else:
        form_data['birth_date'] = ''
    for field in settings.SIMPLE_POPOLO_FIELDS:
        setattr(person, field.name, form_data[field.name])
    for field in ComplexPopoloField.objects.all():
        person_extra.update_complex_field(field, form_data[field.name])
    for extra_field in ExtraField.objects.all():
        if extra_field.key in form_data:
            PersonExtraFieldValue.objects.update_or_create(
                person=person, field=extra_field,
                defaults={'value': form_data[extra_field.key]}
            )
    person.save()
    person_extra.save()
    try:
        update_twitter_user_id(person)
    except TwitterAPITokenMissing:
        pass
    for election_data in form.elections_with_fields:
        # Interpret the form data relating to this election:
        post_id = form_data.get('constituency_' + election_data.slug)
        standing = form_data.pop('standing_' + election_data.slug, 'standing')
        if post_id:
            party_set = PartySet.objects.get(postextra__slug=post_id)
            party_key = 'party_' + party_set.slug + '_' + election_data.slug
            position_key = \
                'party_list_position_' + party_set.slug + '_' + election_data.slug
            party = Organization.objects.get(pk=form_data[party_key])
            party_list_position = form_data.get(position_key) or None
            post = Post.objects.get(extra__slug=post_id)
        else:
            party = None
            party_list_position = None
            post = None
        # Now update the candidacies and not_standing based on those values:
        if standing == 'standing':
            mark_as_standing(
                person_extra, election_data, post, party, party_list_position)
        elif standing == 'not-standing':
            mark_as_not_standing(person_extra, election_data, post)
        else:
            mark_as_unsure_if_standing(person_extra, election_data, post)


def mark_as_standing(person_extra, election_data, post, party, party_list_position):
    # First, if the person is marked as "not standing" in that
    # election, remove that record:
    person_extra.not_standing.remove(election_data)
    membership_ids_to_remove = set()
    membership = None
    # This person might already be marked as standing for this
    # post. In that case, we need to make sure we preserve that
    # existing membership, since there may be metadata attached to it
    # (such as the extra.elected property or CandidateResult records)
    # which would be lost if we deleted and recreated the membership.
    # Go through the person's existing candidacies for this election:
    for existing_membership in Membership.objects.filter(
        extra__post_election__election=election_data,
        role=election_data.candidate_membership_role,
        person__extra=person_extra,
    ):
        if existing_membership.post == post:
            membership = existing_membership
        else:
            membership_ids_to_remove.add(existing_membership.id)
    # If there was no existing membership, we need to create one:
    if not membership:
        membership = Membership.objects.create(
            post=post,
            person=person_extra.base,
            role=election_data.candidate_membership_role,
        )
        MembershipExtra.objects.create(
            base=membership,
            post_election=election_data.postextraelection_set.get(
                postextra=post.extra)
        )
    # Update the party list position in case it's changed:
    membership_extra = membership.extra
    membership_extra.party_list_position = party_list_position
    membership_extra.save()
    # Update the party, in case it's changed:
    membership.on_behalf_of = party
    membership.save()
    # Now remove any memberships that shouldn't now be there:
    for membership_to_remove in Membership.objects.filter(
            pk__in=membership_ids_to_remove):
        raise_if_unsafe_to_delete(membership_to_remove)
        membership_to_remove.delete()


def mark_as_not_standing(person_extra, election_data, post):
    # Remove any existing candidacy:
    for membership in Membership.objects.filter(
        extra__post_election__election=election_data,
        role=election_data.candidate_membership_role,
        person__extra=person_extra,
        # n.b. we are planning to make "not standing" post
        # specific in the future, in which case we would also want
        # this line:
        # post__extra__slug=post_slug,
    ):
        raise_if_unsafe_to_delete(membership)
        membership.delete()
    from .constraints import check_no_candidancy_for_election
    check_no_candidancy_for_election(person_extra.base, election_data)
    person_extra.not_standing.add(election_data)


def mark_as_unsure_if_standing(person_extra, election_data, post):
    # Remove any existing candidacy:
    for membership in Membership.objects.filter(
        extra__election=election_data,
        role=election_data.candidate_membership_role,
        person__extra=person_extra
    ):
        raise_if_unsafe_to_delete(membership)
        membership.delete()
    # Now remove any entry that indicates that they're standing in
    # this election:
    person_extra.not_standing.remove(election_data)


class UnsafeToDelete(Exception):
    pass


def raise_if_unsafe_to_delete(base_object):
    if not paired_object_safe_to_delete(base_object):
        msg = 'Trying to delete a {model} (pk={pk}) that other ' \
              'objects that depend on'
        raise UnsafeToDelete(msg.format(
            model=base_object._meta.model.__name__,
            pk=base_object.id))


def paired_object_safe_to_delete(base_object):
    collector = NestedObjects(using='default')
    collector.collect([base_object])
    collected = collector.nested()
    if len(collected) > 2:
        return False
    assert collected[0] == base_object
    if len(collected[1]) != 1:
        return False
    assert collected[1][0] == base_object.extra
    return True


def squash_whitespace(s):
    # Take any run of more than one whitespace character, and replace
    # it either with a newline (if that replaced text contained a
    # newline) or a space (otherwise).
    return re.sub(
        r'(?ims)\s+',
        lambda m: '\n' if '\n' in m.group(0) else ' ',
        s)


class localparserinfo(parser.parserinfo):
    MONTHS = [
        ('Jan', _l('Jan'), 'January', _l('January')),
        ('Feb', _l('Feb'), 'February', _l('February')),
        ('Mar', _l('Mar'), 'March', _l('March')),
        ('Apr', _l('Apr'), 'April', _l('April')),
        ('May', _l('May'), 'May', _l('May')),
        ('Jun', _l('Jun'), 'June', _l('June')),
        ('Jul', _l('Jul'), 'July', _l('July')),
        ('Aug', _l('Aug'), 'August', _l('August')),
        ('Sep', _l('Sep'), 'Sept', 'September', _l('September')),
        ('Oct', _l('Oct'), 'October', _l('October')),
        ('Nov', _l('Nov'), 'November', _l('November')),
        ('Dec', _l('Dec'), 'December', _l('December'))
    ]

    PERTAIN = ['of', _l('of')]


def parse_approximate_date(s):
    """Take any reasonable date string, and return an ApproximateDate for it

    >>> ad = parse_approximate_date('2014-02-17')
    >>> type(ad)
    <class 'django_date_extensions.fields.ApproximateDate'>
    >>> ad
    2014-02-17
    >>> parse_approximate_date('2014-02')
    2014-02-00
    >>> parse_approximate_date('2014')
    2014-00-00
    >>> parse_approximate_date('future')
    future
    """

    for regexp in [
        r'^(\d{4})-(\d{2})-(\d{2})$',
        r'^(\d{4})-(\d{2})$',
        r'^(\d{4})$'
    ]:
        m = re.search(regexp, s)
        if m:
            return ApproximateDate(*(int(g, 10) for g in m.groups()))
    if s == 'future':
        return ApproximateDate(future=True)
    if s:
        dt = parser.parse(
            s,
            parserinfo=localparserinfo(),
            dayfirst=settings.DD_MM_DATE_FORMAT_PREFERRED
        )
        return ApproximateDate(dt.year, dt.month, dt.day)
    raise ValueError("Couldn't parse '{0}' as an ApproximateDate".format(s))


class PersonExtraQuerySet(models.QuerySet):

    def missing(self, field):
        people_in_current_elections = self.filter(
            base__memberships__extra__post_election__election__current=True
        )
        # The field can be one of several types:
        simple_field = [
            f for f in settings.SIMPLE_POPOLO_FIELDS
            if f.name == field
        ]
        if simple_field:
            return people_in_current_elections.filter(**{'base__' + field: ''})
        complex_field = ComplexPopoloField.objects.filter(name=field).first()
        if complex_field:
            kwargs = {
                'base__{relation}__{key}'.format(
                    relation=complex_field.popolo_array,
                    key=complex_field.info_type_key
                ):
                complex_field.info_type
            }
            return people_in_current_elections.exclude(**kwargs)
        extra_field = ExtraField.objects.filter(key=field).first()
        if extra_field:
            # This case is a bit more complicated because the
            # PersonExtraFieldValue class allows a blank value.
            pefv_completed = PersonExtraFieldValue.objects.filter(
                field=extra_field
            ).exclude(value='')
            return people_in_current_elections.exclude(
                base__id__in=[pefv.person_id for pefv in pefv_completed]
            )
        # If we get to this point, it's a non-existent field on the person:
        raise ValueError("Unknown field '{0}'".format(field))

    def joins_for_csv_output(self):
        return self.select_related('base') \
            .prefetch_related(
                models.Prefetch(
                    'base__memberships',
                    Membership.objects.select_related(
                        'extra',
                        'extra__post_election__election',
                        'on_behalf_of__extra',
                        'post__area',
                        'post__extra',
                    ).prefetch_related(
                        'on_behalf_of__identifiers',
                        'post__area__other_identifiers',
                    )
                ),
                'base__contact_details',
                'base__identifiers',
                'base__links',
                'images__extra__uploading_user',
                models.Prefetch(
                    'base__extra_field_values',
                    PersonExtraFieldValue.objects \
                    .select_related('field')
                ),
            )


class MultipleTwitterIdentifiers(Exception):
    pass


class VersionNotFound(Exception):
    pass


@python_2_unicode_compatible
class PersonExtra(HasImageMixin, models.Model):
    base = models.OneToOneField(Person, related_name='extra')

    # This field stores JSON data with previous version information
    # (as it did in PopIt).
    versions = models.TextField(blank=True)

    images = GenericRelation(Image)

    objects = PersonExtraQuerySet.as_manager()

    @cached_property
    def complex_popolo_fields(self):
        return get_complex_popolo_fields()

    def __getattr__(self, name):
        # We don't want to trigger the population of the
        # complex_popolo_fields property just because Django is
        # checking whether the prefetch objects cache is there:
        if name == '_prefetched_objects_cache':
            return super(PersonExtra, self).__getattr__(self, name)
        field = self.complex_popolo_fields.get(name)
        if field:
            # Iterate rather than using filter because that would
            # cause an extra query when the relation has already been
            # populated via select_related:
            for e in getattr(self.base, field.popolo_array).all():
                info_type_key = getattr(e, field.info_type_key)
                if (info_type_key == field.info_type) or \
                   (info_type_key == field.old_info_type):
                    return getattr(e, field.info_value_key)
            return ''
        else:
            message = _("'PersonExtra' object has no attribute '{name}'")
            raise AttributeError(message.format(name=name))

    def get_slug(self):
        return slugify(self.base.name)

    @property
    def last_name_guess(self):
        try:
            return self.base.name.strip().split(' ')[-1]
        except:
            return self.base.name

    def get_absolute_url(self, request=None):
        path = reverse(
            'person-view',
            kwargs={
                'person_id': self.base.id,
                'ignored_slug': self.get_slug(),
            }
        )
        if request is None:
            return path
        return request.build_absolute_uri(path)

    def get_identifier(self, scheme):
        identifier_object = self.base.identifiers.filter(
            scheme='uk.org.publicwhip').first()
        if identifier_object:
            return identifier_object.identifier
        return ''

    @property
    def current_candidacies(self):
        result = self.base.memberships.filter(
            extra__post_election__election__current=True,
            role=models.F('extra__post_election__election__candidate_membership_role')
        ).select_related('person', 'on_behalf_of', 'post', 'extra') \
            .prefetch_related('post__extra')
        return list(result)

    @property
    def last_candidacy(self):
        ordered_candidacies = Membership.objects. \
            filter(
                person=self.base,
                extra__post_election__election__isnull=False,
            ).order_by('extra__post_election__election__current',
                 'extra__post_election__election__election_date'
            )
        return ordered_candidacies.last()

    def last_party(self):
        last_candidacy = self.last_candidacy
        if last_candidacy is None:
            return None
        return last_candidacy.on_behalf_of

    def name_with_honorifics(self):
        name_parts = []
        pre = self.base.honorific_prefix
        post = self.base.honorific_suffix
        if pre:
            name_parts.append(pre)
        name_parts.append(self.base.name)
        if post:
            name_parts.append(post)
        return ' '.join(name_parts)

    @property
    def dob_as_approximate_date(self):
        return parse_approximate_date(self.base.birth_date)

    def dob_as_date(self):
        approx = self.dob_as_approximate_date
        return date(approx.year, approx.month, approx.day)

    @property
    def age(self):
        """Return a string representing the person's age"""

        dob = self.dob_as_approximate_date
        if not dob:
            return None
        today = date.today()
        approx_age = today.year - dob.year
        if dob.month == 0 and dob.day == 0:
            min_age = approx_age - 1
            max_age = approx_age
        elif dob.day == 0:
            min_age = approx_age - 1
            max_age = approx_age
            if today.month < dob.month:
                max_age = min_age
            elif today.month > dob.month:
                min_age = max_age
        else:
            # There's a complete date:
            dob_as_date = self.dob_as_date()
            try:
                today_in_birth_year = date(dob.year, today.month, today.day)
            except ValueError:
                # It must have been February 29th
                today_in_birth_year = date(dob.year, 3, 1)
            if today_in_birth_year > dob_as_date:
                min_age = max_age = today.year - dob.year
            else:
                min_age = max_age = (today.year - dob.year) -1
        if min_age == max_age:
            # We know their exact age:
            return str(min_age)
        return _("{min_age} or {max_age}").format(min_age=min_age,
                                                  max_age=max_age)

    """
    Return the elected state for a person in an election.
    Takes the election object as an arg.
    Returns True if they were elected, False if not and None if
    the results have not been set.
    This assumes that someone can only be elected in a single
    post in any election.
    """
    def get_elected(self, election):
        role = election.candidate_membership_role
        if role is None:
            role = ''
        membership = self.base.memberships \
            .select_related('extra') \
            .filter(
                role=role,
                extra__post_election__election=election,
            )

        result = membership.first()
        if result:
            return result.extra.elected

        return None

    @property
    def twitter_identifiers(self):
        screen_name = None
        user_id = None
        # Get the Twitter screen name and user ID if they exist:
        try:
            screen_name = self.base.contact_details \
                .get(contact_type='twitter').value
        except ContactDetail.DoesNotExist:
            screen_name = None
        except ContactDetail.MultipleObjectsReturned:
            msg = "Multiple Twitter screen names found for {name} ({id})"
            raise MultipleTwitterIdentifiers(
                _(msg).format(name=self.base.name, id=self.base.id))
        try:
            user_id = self.base.identifiers \
                .get(scheme='twitter').identifier
        except Identifier.DoesNotExist:
            user_id = None
        except Identifier.MultipleObjectsReturned:
            msg = "Multiple Twitter user IDs found for {name} ({id})"
            raise MultipleTwitterIdentifiers(
                _(msg).format(name=self.base.name, id=self.base.id))
        return user_id, screen_name

    @property
    def version_diffs(self):
        versions = self.versions
        if not versions:
            versions = []
        return get_version_diffs(json.loads(versions))

    def diff_for_version(self, version_id, inline_style=False):
        versions = self.versions or []
        all_version_diffs = get_version_diffs(json.loads(versions))
        right_version_diff = None
        for version_diff in all_version_diffs:
            if version_diff['version_id'] == version_id:
                right_version_diff = version_diff
                break
        if not right_version_diff:
            msg = "Couldn't find version {0} for person with ID {1}"
            raise VersionNotFound(msg.format(version_id, self.base.id))
        template = loader.get_template('candidates/_diffs_against_parents.html')
        rendered = template.render({
            'diffs_against_all_parents': right_version_diff['diffs'],
            'inline_style': inline_style,
        })
        return squash_whitespace('<dl>{0}</dl>'.format(rendered))

    def record_version(self, change_metadata, new_person=False):
        versions = []
        if self.versions:
            versions = json.loads(self.versions)
        new_version = change_metadata.copy()
        new_version['data'] = get_person_as_version_data(
            self.base, new_person=new_person)
        versions.insert(0, new_version)
        self.versions = json.dumps(versions)

    def update_complex_field(self, location, new_value):
        existing_info_types = [location.info_type]
        if location.old_info_type:
            existing_info_types.append(location.old_info_type)
        related_manager = getattr(self.base, location.popolo_array)
        # Remove the old entries of that type:
        kwargs = {
            (location.info_type_key + '__in'): existing_info_types
        }
        related_manager.filter(**kwargs).delete()
        if new_value:
            kwargs = {
                location.info_type_key: location.info_type,
                location.info_value_key: new_value,
            }
            related_manager.create(**kwargs)

    def get_initial_form_data(self):
        initial_data = {}
        for field in settings.SIMPLE_POPOLO_FIELDS:
            initial_data[field.name] = getattr(self.base, field.name)
        for field in ComplexPopoloField.objects.all():
            initial_data[field.name] = getattr(self, field.name)
        for extra_field_value in PersonExtraFieldValue.objects.filter(
                person=self.base
        ).select_related('field'):
            initial_data[extra_field_value.field.key] = extra_field_value.value
        not_standing_elections = list(self.not_standing.all())

        for election_data in Election.objects.current().filter(
                postextraelection__membershipextra__base__person=self.base
            ).by_date():
            constituency_key = 'constituency_' + election_data.slug
            standing_key = 'standing_' + election_data.slug
            try:
                candidacy = MembershipExtra.objects.get(
                    post_election__election=election_data,
                    base__person__extra=self
                )
            except MembershipExtra.DoesNotExist:
                candidacy = None
            if election_data in not_standing_elections:
                initial_data[standing_key] = 'not-standing'
            elif candidacy:
                initial_data[standing_key] = 'standing'
                post_id = candidacy.base.post.extra.slug
                initial_data[constituency_key] = post_id
                party_set = PartySet.objects.get(postextra__slug=post_id)
                party = candidacy.base.on_behalf_of
                party_key = 'party_' + party_set.slug + '_' + election_data.slug
                initial_data[party_key] = party.id
                position = candidacy.party_list_position
                position_key = 'party_list_position_' + party_set.slug + '_' + election_data.slug
                if position:
                    initial_data[position_key] = position
            else:
                initial_data[standing_key] = 'not-sure'
                initial_data[constituency_key] = ''
        return initial_data

    def update_from_form(self, form):
        update_person_from_form(self.base, self, form)

    @classmethod
    def create_from_form(cls, form):
        person = Person.objects.create(
            name=form.cleaned_data['name'],
        )
        person_extra = PersonExtra.objects.create(
            base=person,
        )
        update_person_from_form(person, person_extra, form)
        return person_extra

    def as_list_of_dicts(self, election, base_url=None, redirects=None):
        result = []
        if not base_url:
            base_url = ''
        if not redirects:
            redirects = {}
        # Find the list of relevant candidacies. So as not to cause
        # extra queries, we don't use filter but instead iterate over
        # all objects:
        candidacies = []
        for m in self.base.memberships.all():
            try:
                m_extra = m.extra
            except ObjectDoesNotExist:
                continue
            if not m_extra.post_election.election:
                continue
            expected_role = m.extra.post_election.election.candidate_membership_role
            if election is None:
                if expected_role == m.role:
                    candidacies.append(m)
            else:
                if m_extra.post_election.election == election and expected_role == m.role:
                    candidacies.append(m)
        for candidacy in candidacies:
            candidacy_extra = candidacy.extra
            party = candidacy.on_behalf_of
            post = candidacy.post
            elected = candidacy_extra.elected
            elected_for_csv = ''
            image_copyright = ''
            image_uploading_user = ''
            image_uploading_user_notes = ''
            proxy_image_url_template = ''
            if elected is not None:
                elected_for_csv = str(elected)
            mapit_url = ''
            primary_image = None
            for image in self.images.all():
                if image.is_primary:
                    primary_image = image
            primary_image_url = None
            if primary_image:
                primary_image_url = urljoin(base_url, primary_image.image.url)
                if settings.IMAGE_PROXY_URL and base_url:
                    encoded_url = quote_plus(primary_image_url)
                    proxy_image_url_template = settings.IMAGE_PROXY_URL + \
                        encoded_url + '/{height}/{width}.{extension}'

                try:
                    image_copyright = primary_image.extra.copyright
                    user = primary_image.extra.uploading_user
                    if user is not None:
                        image_uploading_user = primary_image.extra.uploading_user.username
                    image_uploading_user_notes = primary_image.extra.user_notes
                except ObjectDoesNotExist:
                    pass
            twitter_user_id = ''
            for identifier in self.base.identifiers.all():
                if identifier.scheme == 'twitter':
                    twitter_user_id = identifier.identifier
            old_person_ids = ';'.join(
                text_type(i) for i in redirects.get(self.base.id, []))

            row = {
                'id': self.base.id,
                'name': self.base.name,
                'honorific_prefix': self.base.honorific_prefix,
                'honorific_suffix': self.base.honorific_suffix,
                'gender': self.base.gender,
                'birth_date': self.base.birth_date,
                'election': candidacy_extra.post_election.election.slug,
                'election_date': candidacy_extra.post_election.election.election_date,
                'election_current': candidacy_extra.post_election.election.current,
                'party_id': party.extra.slug,
                'party_lists_in_use': candidacy_extra.post_election.election.party_lists_in_use,
                'party_list_position': candidacy_extra.party_list_position,
                'party_name': party.name,
                'post_id': post.extra.slug,
                'post_label': post.extra.short_label,
                'mapit_url': mapit_url,
                'elected': elected_for_csv,
                'email': self.base.email,
                'twitter_username': self.twitter_username,
                'twitter_user_id': twitter_user_id,
                'facebook_page_url': self.facebook_page_url,
                'linkedin_url': self.linkedin_url,
                'party_ppc_page_url': self.party_ppc_page_url,
                'facebook_personal_url': self.facebook_personal_url,
                'homepage_url': self.homepage_url,
                'wikipedia_url': self.wikipedia_url,
                'image_url': primary_image_url,
                'proxy_image_url_template': proxy_image_url_template,
                'image_copyright': image_copyright,
                'image_uploading_user': image_uploading_user,
                'image_uploading_user_notes': image_uploading_user_notes,
                'old_person_ids': old_person_ids,
            }
            from ..election_specific import get_extra_csv_values
            extra_csv_data = get_extra_csv_values(self.base, election, post)
            row.update(extra_csv_data)
            result.append(row)

        return result

    not_standing = models.ManyToManyField(
        Election, related_name='persons_not_standing'
    )

    def __str__(self):
        # WARNING: This will cause an extra query when getting the
        # repr() or unicode() of this object unless the base object
        # has been select_related.
        return self.base.name


@python_2_unicode_compatible
class OrganizationExtra(HasImageMixin, models.Model):
    base = models.OneToOneField(Organization, related_name='extra')
    slug = models.CharField(max_length=256, blank=True, unique=True)

    # For parties, which party register is it on:
    register = models.CharField(blank=True, max_length=512)

    images = GenericRelation(Image)

    def __str__(self):
        # WARNING: This will cause an extra query when getting the
        # repr() or unicode() of this object unless the base object
        # has been select_related.
        return self.base.name

    def ec_id(self):
        try:
            party_id = self.base.identifiers.filter(
                scheme="electoral-commission").first()
            return party_id.identifier
        except:
            return "ynmp-party:2"



@python_2_unicode_compatible
class PostExtra(HasImageMixin, models.Model):
    base = models.OneToOneField(Post, related_name='extra')
    slug = models.CharField(max_length=256, blank=True, unique=True)

    elections = models.ManyToManyField(
        Election,
        related_name='posts',
        through='PostExtraElection'
    )
    group = models.CharField(max_length=1024, blank=True)
    party_set = models.ForeignKey('PartySet', blank=True, null=True)

    def __str__(self):
        # WARNING: This will cause an extra query when getting the
        # repr() or unicode() of this object unless the base object
        # has been select_related.
        return self.base.label

    @property
    def short_label(self):
        from candidates.election_specific import shorten_post_label
        return shorten_post_label(self.base.label)


class PostExtraElection(models.Model):
    postextra = models.ForeignKey(PostExtra)
    election = models.ForeignKey(Election)
    ballot_paper_id = models.CharField(blank=True, max_length=255, unique=True)

    candidates_locked = models.BooleanField(default=False)
    winner_count = models.IntegerField(blank=True, null=True)

    class Meta:
        unique_together = ('election', 'postextra')

    def __repr__(self):
        fmt = "<PostExtraElection ballot_paper_id='{e}'{l}{w}>"
        return fmt.format(
            e=self.ballot_paper_id,
            l=(' candidates_locked=True' if self.candidates_locked else ''),
            w=(' winner_count={0}'.format(self.winner_count)
               if (self.winner_count is not None) else ''))

    def get_absolute_url(self):
        return reverse('constituency', args=[
            self.election.slug,
            self.postextra.slug,
            slugify(self.postextra.base.label)
        ])


class MembershipExtra(models.Model):
    base = models.OneToOneField(Membership, related_name='extra')

    elected = models.NullBooleanField()
    party_list_position = models.IntegerField(null=True)
    post_election = models.ForeignKey('candidates.PostExtraElection')

    def save(self, *args, **kwargs):
        if self.post_election and getattr(self, 'check_for_broken', True):
            if self.post_election.election in self.base.person.extra.not_standing.all():
                msg = 'Trying to add a MembershipExtra with an election ' \
                      '"{election}", but that\'s in {person} ' \
                      '({person_id})\'s not_standing list.'
                raise Exception(msg.format(
                    election=self.post_election.election,
                    person=self.base.person.name,
                    person_id=self.base.person.id))
        super(MembershipExtra, self).save(*args, **kwargs)


@python_2_unicode_compatible
class AreaExtra(models.Model):
    base = models.OneToOneField(Area, related_name='extra')

    type = models.ForeignKey(AreaType, blank=True, null=True, related_name='areas')

    def __str__(self):
        # WARNING: This will cause an extra query when getting the
        # repr() or unicode() of this object unless the base object
        # has been select_related.
        return self.base.name


@python_2_unicode_compatible
class PartySet(models.Model):
    slug = models.CharField(max_length=256, unique=True)
    name = models.CharField(max_length=1024)
    parties = models.ManyToManyField(Organization, related_name='party_sets')

    def __str__(self):
        return self.name

    def party_choices_basic(self):
        result = list(self.parties.order_by('name').values_list('id', 'name'))
        result.insert(0, ('', ''))
        return result

    def party_choices(self,
            include_descriptions=True, exclude_deregistered=False,
            include_description_ids=False, include_non_current=True):
        # For various reasons, we've found it's best to order the
        # parties by those that have the most candidates - this means
        # that the commonest parties to select are at the top of the
        # drop down.  The logic here tries to build such an ordered
        # list of candidates if there are enough that such an ordering
        # makes sense.  Otherwise the fallback is to rank
        # alphabetically.

        candidacies_ever_qs = self.parties.all().annotate(
                membership_count=models.Count('memberships_on_behalf_of__pk')
            ).order_by('-membership_count', 'name').only('end_date', 'name')

        parties_current_qs = self.parties.filter(
            memberships_on_behalf_of__extra__post_election__election__current=True
            ).annotate(
                membership_count=models.Count('memberships_on_behalf_of__pk')
            ).order_by('-membership_count', 'name').only('end_date', 'name')

        if not include_non_current:
            parties_current_qs = parties_current_qs.exclude(membership_count=0)

        parties_notcurrent_qs = self.parties.filter(
                ~models.Q(
                    memberships_on_behalf_of__extra__post_election__election__current=True)
            ).annotate(
                membership_count=models.Value(0, models.IntegerField()),
            ).order_by('-membership_count', 'name').only('end_date', 'name')


        minimum_count = settings.CANDIDATES_REQUIRED_FOR_WEIGHTED_PARTY_LIST

        total_memberships = MembershipExtra.objects.all()
        current_memberships = total_memberships.filter(post_election__election__current=True)

        queries = []
        if current_memberships.count() > minimum_count:
            queries.append(parties_current_qs)
            if include_non_current:
                queries.append(parties_notcurrent_qs)
        elif total_memberships.count() > minimum_count:
            queries.append(candidacies_ever_qs)
        else:
            return self.party_choices_basic()

        result = [('', '')]
        parties_with_candidates = []

        for qs in queries:
            if include_descriptions:
                qs = qs.prefetch_related('other_names')
            for party in qs:
                parties_with_candidates.append(party)
                count_string = ""
                if party.membership_count:
                    count_string = " ({} candidates)".format(
                        party.membership_count)

                name = _('{party_name}{count_string}').format(
                    party_name=party.name,
                    count_string=count_string
                )

                if party.end_date:
                    party_end_date = parser.parse(party.end_date).date()
                    if date.today() > party_end_date:
                        if exclude_deregistered:
                            continue
                        name = "{} (Deregistered {})".format(
                            name, party.end_date
                        )

                if include_descriptions and party.other_names.exists():
                    names = [(party.pk, party.name),]
                    for other_name in party.other_names.all():
                        joint_text = re.compile(r'joint descriptions? with')
                        party_id_str = str(party.pk)
                        if include_description_ids:
                            party_id_str = "{}__{}".format(
                                party_id_str,
                                other_name.pk
                            )
                        if not joint_text.search(other_name.name.lower()):
                            names.append((party_id_str, other_name.name))
                    party_names = (name, (names))
                else:
                    party_names = (str(party.pk), name)


                result.append(party_names)
        return result


class ImageExtraManager(models.Manager):

    def create_from_file(
            self, image_filename, ideal_relative_name, base_kwargs, extra_kwargs
    ):
        # Import the file to media root and create the ORM
        # objects.
        storage = FileSystemStorage()
        desired_storage_path = join('images', ideal_relative_name)
        with open(image_filename, 'rb') as f:
            storage_filename = storage.save(desired_storage_path, f)
        image = Image.objects.create(image=storage_filename, **base_kwargs)
        return ImageExtra.objects.create(base=image, **extra_kwargs)

    def update_or_create_from_file(
            self, image_filename, ideal_relative_name, defaults, **kwargs
    ):
        try:
            image_extra = ImageExtra.objects \
                .select_related('base').get(**kwargs)
            for k, v in defaults.items():
                if k.startswith('base__'):
                    base_k = re.sub(r'^base__', '', k)
                    setattr(image_extra.base, base_k, v)
                else:
                    setattr(image_extra, k, v)
            image_extra.save()
            image_extra.base.save()
            return image_extra, False
        except ImageExtra.DoesNotExist:
            # Prepare args for the base object first:
            base_kwargs = {
                re.sub(r'base__', '', k): v for k, v in defaults.items()
                if k.startswith('base__')
            }
            base_kwargs.update({
                re.sub(r'base__', '', k): v for k, v in kwargs.items()
                if k.startswith('base__')
            })
            # And now the extra object:
            extra_kwargs = {
                k: v for k, v in defaults.items() if not k.startswith('base__')
            }
            extra_kwargs.update({
                k: v for k, v in kwargs.items() if not k.startswith('base__')
            })
            image_extra = self.create_from_file(
                image_filename, ideal_relative_name, base_kwargs, extra_kwargs
            )
        return image_extra


class ImageExtra(models.Model):
    base = models.OneToOneField(Image, related_name='extra')

    copyright = models.CharField(max_length=64, default='other', blank=True)
    uploading_user = models.ForeignKey(User, blank=True, null=True)
    user_notes = models.TextField(blank=True)
    md5sum = models.CharField(max_length=32, blank=True)
    user_copyright = models.CharField(max_length=128, blank=True)
    notes = models.TextField(blank=True)

    objects = ImageExtraManager()
