from datetime import date

try:
    from django.contrib.contenttypes.fields import GenericRelation
except ImportError:
    # This fallback import is the version that was deprecated in
    # Django 1.7 and is removed in 1.9:
    from django.contrib.contenttypes.generic import GenericRelation

try:
    # PassTrhroughManager was removed in django-model-utils 2.4
    # see issue #22 at https://github.com/openpolis/django-popolo/issues/22
    from model_utils.managers import PassThroughManager
except ImportError:
    pass

import json
from slugify import slugify

from django.core.validators import RegexValidator
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template import loader
from django.db import models
from django.utils.functional import cached_property
from django.utils.six.moves.urllib_parse import urljoin, quote_plus
from django.utils.six import text_type
from model_utils import Choices
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_save
from django.dispatch import receiver
from images.models import HasImageMixin

from candidates.diffs import get_version_diffs
from candidates.models import ComplexPopoloField, PersonExtraFieldValue

from .behaviors.models import Timestampable, Dateframeable, GenericRelatable
from .querysets import (
    PostQuerySet,
    OtherNameQuerySet,
    ContactDetailQuerySet,
    MembershipQuerySet,
    OrganizationQuerySet,
    PersonQuerySet,
)


class MultipleTwitterIdentifiers(Exception):
    pass


class VersionNotFound(Exception):
    pass


class Person(HasImageMixin, Dateframeable, Timestampable, models.Model):
    """
    A real person, alive or dead
    see schema at http://popoloproject.com/schemas/person.json#
    """

    json_ld_context = "http://popoloproject.com/contexts/person.jsonld"
    json_ld_type = "http://www.w3.org/ns/person#Person"

    name = models.CharField(
        _("name"), max_length=512, help_text=_("A person's preferred full name")
    )

    # array of itemss referencing "http://popoloproject.com/schemas/other_name.json#"
    other_names = GenericRelation(
        "OtherName", help_text="Alternate or former names"
    )

    # array of items referencing "http://popoloproject.com/schemas/identifier.json#"
    identifiers = GenericRelation("Identifier", help_text="Issued identifiers")

    family_name = models.CharField(
        _("family name"),
        max_length=128,
        blank=True,
        help_text=_("One or more family names"),
    )
    given_name = models.CharField(
        _("given name"),
        max_length=128,
        blank=True,
        help_text=_("One or more primary given names"),
    )
    additional_name = models.CharField(
        _("additional name"),
        max_length=128,
        blank=True,
        help_text=_("One or more secondary given names"),
    )
    honorific_prefix = models.CharField(
        _("honorific prefix"),
        max_length=128,
        blank=True,
        help_text=_("One or more honorifics preceding a person's name"),
    )
    honorific_suffix = models.CharField(
        _("honorific suffix"),
        max_length=128,
        blank=True,
        help_text=_("One or more honorifics following a person's name"),
    )
    patronymic_name = models.CharField(
        _("patronymic name"),
        max_length=128,
        blank=True,
        help_text=_("One or more patronymic names"),
    )
    sort_name = models.CharField(
        _("sort name"),
        max_length=128,
        blank=True,
        help_text=_("A name to use in an lexicographically ordered list"),
    )
    email = models.EmailField(
        _("email"),
        blank=True,
        null=True,
        help_text=_("A preferred email address"),
    )
    gender = models.CharField(
        _("gender"), max_length=128, blank=True, help_text=_("A gender")
    )
    birth_date = models.CharField(
        _("birth date"),
        max_length=10,
        blank=True,
        help_text=_("A date of birth"),
    )
    death_date = models.CharField(
        _("death date"),
        max_length=10,
        blank=True,
        help_text=_("A date of death"),
    )
    image = models.URLField(
        _("image"), blank=True, null=True, help_text=_("A URL of a head shot")
    )
    summary = models.CharField(
        _("summary"),
        max_length=1024,
        blank=True,
        help_text=_("A one-line account of a person's life"),
    )
    biography = models.TextField(
        _("biography"),
        blank=True,
        help_text=_("An extended account of a person's life"),
    )
    national_identity = models.CharField(
        _("national identity"),
        max_length=128,
        blank=True,
        null=True,
        help_text=_("A national identity"),
    )

    # array of items referencing "http://popoloproject.com/schemas/contact_detail.json#"
    contact_details = GenericRelation(
        "ContactDetail", help_text="Means of contacting the person"
    )

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = GenericRelation(
        "Link", help_text="URLs to documents related to the person"
    )

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    sources = GenericRelation(
        "Source", help_text="URLs to source documents about the person"
    )

    # Former 'extra' fields
    # This field stores JSON data with previous version information
    # (as it did in PopIt).
    versions = models.TextField(blank=True)
    images = GenericRelation("images.Image")
    not_standing = models.ManyToManyField(
        "elections.Election", related_name="persons_not_standing"
    )

    class Meta:
        verbose_name_plural = "People"

    try:
        # PassTrhroughManager was removed in django-model-utils 2.4, see issue #22
        objects = PassThroughManager.for_queryset_class(PersonQuerySet)()
    except:
        objects = PersonQuerySet.as_manager()

    def add_contact_detail(self, **kwargs):
        c = ContactDetail(content_object=self, **kwargs)
        c.save()

    def add_contact_details(self, contacts):
        for c in contacts:
            self.add_contact_detail(**c)

    @cached_property
    def complex_popolo_fields(self):
        from candidates.models.fields import get_complex_popolo_fields

        return get_complex_popolo_fields()

    @property
    def current_candidacies(self):
        result = self.memberships.filter(
            post_election__election__current=True
        ).select_related("person", "party", "post")
        return list(result)

    def record_version(self, change_metadata, new_person=False):
        # Needed because of a circular import
        from candidates.models.versions import get_person_as_version_data

        versions = []
        if self.versions:
            versions = json.loads(self.versions)
        new_version = change_metadata.copy()
        new_version["data"] = get_person_as_version_data(
            self, new_person=new_person
        )
        versions.insert(0, new_version)
        self.versions = json.dumps(versions)

    def get_slug(self):
        return slugify(self.name)

    @property
    def last_name_guess(self):
        try:
            return self.base.name.strip().split(" ")[-1]
        except:
            return self.base.name

    def get_absolute_url(self, request=None):
        path = reverse(
            "person-view",
            kwargs={"person_id": self.pk, "ignored_slug": self.get_slug()},
        )
        if request is None:
            return path
        return request.build_absolute_uri(path)

    def get_identifier(self, scheme):
        identifier_object = self.identifiers.filter(
            scheme="uk.org.publicwhip"
        ).first()
        if identifier_object:
            return identifier_object.identifier
        return ""

    @property
    def last_candidacy(self):
        ordered_candidacies = Membership.objects.filter(
            person=self, post_election__election__isnull=False
        ).order_by(
            "post_election__election__current",
            "post_election__election__election_date",
        )
        return ordered_candidacies.last()

    def last_party(self):
        last_candidacy = self.last_candidacy
        if last_candidacy is None:
            return None
        return last_candidacy.party

    def name_with_honorifics(self):
        name_parts = []
        pre = self.honorific_prefix
        post = self.honorific_suffix
        if pre:
            name_parts.append(pre)
        name_parts.append(self.name)
        if post:
            name_parts.append(post)
        return " ".join(name_parts)

    @property
    def dob_as_approximate_date(self):
        from popolo.person_helpers import parse_approximate_date

        return parse_approximate_date(self.birth_date)

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
                min_age = max_age = (today.year - dob.year) - 1
        if min_age == max_age:
            # We know their exact age:
            return str(min_age)
        return _("{min_age} or {max_age}").format(
            min_age=min_age, max_age=max_age
        )

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
            role = ""
        membership = self.memberships.filter(
            role=role, post_election__election=election
        )

        result = membership.first()
        if result:
            return result.elected

        return None

    @property
    def twitter_identifiers(self):
        screen_name = None
        user_id = None
        # Get the Twitter screen name and user ID if they exist:
        try:
            screen_name = self.contact_details.get(contact_type="twitter").value
        except ContactDetail.DoesNotExist:
            screen_name = None
        except ContactDetail.MultipleObjectsReturned:
            msg = "Multiple Twitter screen names found for {name} ({id})"
            raise MultipleTwitterIdentifiers(
                _(msg).format(name=self.name, id=self.id)
            )
        try:
            user_id = self.identifiers.get(scheme="twitter").identifier
        except Identifier.DoesNotExist:
            user_id = None
        except Identifier.MultipleObjectsReturned:
            msg = "Multiple Twitter user IDs found for {name} ({id})"
            raise MultipleTwitterIdentifiers(
                _(msg).format(name=self.name, id=self.id)
            )
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
            if version_diff["version_id"] == version_id:
                right_version_diff = version_diff
                break
        if not right_version_diff:
            msg = "Couldn't find version {0} for person with ID {1}"
            raise VersionNotFound(msg.format(version_id, self.id))
        template = loader.get_template("candidates/_diffs_against_parents.html")
        rendered = template.render(
            {
                "diffs_against_all_parents": right_version_diff["diffs"],
                "inline_style": inline_style,
            }
        )
        from .person_helpers import squash_whitespace

        return squash_whitespace("<dl>{}</dl>".format(rendered))

    def update_complex_field(self, location, new_value):
        existing_info_types = [location.info_type]
        if location.old_info_type:
            existing_info_types.append(location.old_info_type)
        related_manager = getattr(self, location.popolo_array)
        # Remove the old entries of that type:
        kwargs = {(location.info_type_key + "__in"): existing_info_types}
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
            initial_data[field.name] = getattr(self, field.name)
        for field in ComplexPopoloField.objects.all():
            initial_data[field.name] = getattr(self, field.name)
        for extra_field_value in PersonExtraFieldValue.objects.filter(
            person=self
        ).select_related("field"):
            initial_data[extra_field_value.field.key] = extra_field_value.value
        not_standing_elections = list(self.not_standing.all())
        from elections.models import Election

        for election_data in (
            Election.objects.current()
            .filter(postextraelection__membership__person=self)
            .by_date()
        ):
            constituency_key = "constituency_" + election_data.slug
            standing_key = "standing_" + election_data.slug
            try:
                candidacy = Membership.objects.get(
                    post_election__election=election_data, person=self
                )
            except Membership.DoesNotExist:
                candidacy = None
            if election_data in not_standing_elections:
                initial_data[standing_key] = "not-standing"
            elif candidacy:
                initial_data[standing_key] = "standing"
                post_id = candidacy.post.slug
                initial_data[constituency_key] = post_id
                from candidates.models import PartySet

                party_set = PartySet.objects.get(post__slug=post_id)
                party = candidacy.party
                party_key = (
                    "party_" + party_set.slug.upper() + "_" + election_data.slug
                )
                initial_data[party_key] = party.ec_id
                position = candidacy.party_list_position
                position_key = (
                    "party_list_position_"
                    + party_set.slug.upper()
                    + "_"
                    + election_data.slug
                )
                if position:
                    initial_data[position_key] = position
            else:
                initial_data[standing_key] = "not-sure"
                initial_data[constituency_key] = ""
        return initial_data

    def update_from_form(self, form):
        from .person_helpers import update_person_from_form

        update_person_from_form(self, form)

    @classmethod
    def create_from_form(cls, form):
        from .person_helpers import update_person_from_form

        person = Person.objects.create(name=form.cleaned_data["name"])

        update_person_from_form(person, form)
        return person

    def as_list_of_dicts(self, election, base_url=None, redirects=None):
        result = []
        if not base_url:
            base_url = ""
        if not redirects:
            redirects = {}
        # Find the list of relevant candidacies. So as not to cause
        # extra queries, we don't use filter but instead iterate over
        # all objects:
        candidacies = []
        for m in self.memberships.all():
            if not m.post_election.election:
                continue
            expected_role = m.post_election.election.candidate_membership_role
            if election is None:
                if expected_role == m.role:
                    candidacies.append(m)
            else:
                if (
                    m.post_election.election == election
                    and expected_role == m.role
                ):
                    candidacies.append(m)
        for candidacy in candidacies:
            party = candidacy.party
            post = candidacy.post
            elected = candidacy.elected
            elected_for_csv = ""
            image_copyright = ""
            image_uploading_user = ""
            image_uploading_user_notes = ""
            proxy_image_url_template = ""
            if elected is not None:
                elected_for_csv = str(elected)
            mapit_url = ""
            primary_image = None
            for image in self.images.all():
                if image.is_primary:
                    primary_image = image
            primary_image_url = None
            if primary_image:
                primary_image_url = urljoin(base_url, primary_image.image.url)
                if settings.IMAGE_PROXY_URL and base_url:
                    encoded_url = quote_plus(primary_image_url)
                    proxy_image_url_template = (
                        settings.IMAGE_PROXY_URL
                        + encoded_url
                        + "/{height}/{width}.{extension}"
                    )

                try:
                    image_copyright = primary_image.extra.copyright
                    user = primary_image.extra.uploading_user
                    if user is not None:
                        image_uploading_user = (
                            primary_image.extra.uploading_user.username
                        )
                    image_uploading_user_notes = primary_image.extra.user_notes
                except ObjectDoesNotExist:
                    pass
            twitter_user_id = ""
            for identifier in self.identifiers.all():
                if identifier.scheme == "twitter":
                    twitter_user_id = identifier.identifier
            old_person_ids = ";".join(
                text_type(i) for i in redirects.get(self.id, [])
            )

            row = {
                "id": self.id,
                "name": self.name,
                "honorific_prefix": self.honorific_prefix,
                "honorific_suffix": self.honorific_suffix,
                "gender": self.gender,
                "birth_date": self.birth_date,
                "election": candidacy.post_election.election.slug,
                "election_date": candidacy.post_election.election.election_date,
                "election_current": candidacy.post_election.election.current,
                "party_id": party.legacy_slug,
                "party_lists_in_use": candidacy.post_election.election.party_lists_in_use,
                "party_list_position": candidacy.party_list_position,
                "party_name": party.name,
                "post_id": post.slug,
                "post_label": post.short_label,
                "mapit_url": mapit_url,
                "elected": elected_for_csv,
                "email": self.email,
                "twitter_username": self.twitter_username,
                "twitter_user_id": twitter_user_id,
                "facebook_page_url": self.facebook_page_url,
                "linkedin_url": self.linkedin_url,
                "party_ppc_page_url": self.party_ppc_page_url,
                "facebook_personal_url": self.facebook_personal_url,
                "homepage_url": self.homepage_url,
                "wikipedia_url": self.wikipedia_url,
                "image_url": primary_image_url,
                "proxy_image_url_template": proxy_image_url_template,
                "image_copyright": image_copyright,
                "image_uploading_user": image_uploading_user,
                "image_uploading_user_notes": image_uploading_user_notes,
                "old_person_ids": old_person_ids,
            }
            from candidates.election_specific import get_extra_csv_values

            extra_csv_data = get_extra_csv_values(self, election, post)
            row.update(extra_csv_data)
            result.append(row)

        return result

    def __getattr__(self, name):
        # We don't want to trigger the population of the
        # complex_popolo_fields property just because Django is
        # checking whether the prefetch objects cache is there:
        if name == "_prefetched_objects_cache":
            return super().__getattr__(self, name)
        field = self.complex_popolo_fields.get(name)
        if field:
            # Iterate rather than using filter because that would
            # cause an extra query when the relation has already been
            # populated via select_related:
            for e in getattr(self, field.popolo_array).all():
                info_type_key = getattr(e, field.info_type_key)
                if (info_type_key == field.info_type) or (
                    info_type_key == field.old_info_type
                ):
                    return getattr(e, field.info_value_key)
            return ""
        else:
            message = _("'Person' object has no attribute '{name}'")
            raise AttributeError(message.format(name=name))

    def __str__(self):
        return self.name


class Organization(HasImageMixin, Dateframeable, Timestampable, models.Model):
    """
    A group with a common purpose or reason for existence that goes beyond the
    set of people belonging to it see schema at
    http://popoloproject.com/schemas/organization.json#
    """

    name = models.CharField(
        _("name"),
        max_length=512,
        help_text=_("A primary name, e.g. a legally recognized name"),
    )
    summary = models.CharField(
        _("summary"),
        max_length=1024,
        blank=True,
        help_text=_("A one-line description of an organization"),
    )
    description = models.TextField(
        _("biography"),
        blank=True,
        help_text=_("An extended description of an organization"),
    )

    # array of items referencing "http://popoloproject.com/schemas/other_name.json#"
    other_names = GenericRelation(
        "OtherName", help_text="Alternate or former names"
    )

    # array of items referencing "http://popoloproject.com/schemas/identifier.json#"
    identifiers = GenericRelation("Identifier", help_text="Issued identifiers")
    classification = models.CharField(
        _("classification"),
        max_length=512,
        blank=True,
        help_text=_("An organization category, e.g. committee"),
    )

    # reference to "http://popoloproject.com/schemas/organization.json#"
    parent = models.ForeignKey(
        "Organization",
        blank=True,
        null=True,
        related_name="children",
        help_text=_("The organization that contains this organization"),
    )

    # reference to "http://popoloproject.com/schemas/area.json#"
    area = models.ForeignKey(
        "Area",
        blank=True,
        null=True,
        related_name="organizations",
        help_text=_(
            "The geographic area to which this organization is related"
        ),
    )

    founding_date = models.CharField(
        _("founding date"),
        max_length=10,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex="^[0-9]{4}(-[0-9]{2}){0,2}$",
                message="founding date must follow the given pattern: ^[0-9]{4}(-[0-9]{2}){0,2}$",
                code="invalid_founding_date",
            )
        ],
        help_text=_("A date of founding"),
    )
    dissolution_date = models.CharField(
        _("dissolution date"),
        max_length=10,
        null=True,
        blank=True,
        validators=[
            RegexValidator(
                regex="^[0-9]{4}(-[0-9]{2}){0,2}$",
                message="dissolution date must follow the given pattern: ^[0-9]{4}(-[0-9]{2}){0,2}$",
                code="invalid_dissolution_date",
            )
        ],
        help_text=_("A date of dissolution"),
    )
    image = models.URLField(
        _("image"),
        blank=True,
        null=True,
        help_text=_("A URL of an image, to identify the organization visually"),
    )

    # array of items referencing "http://popoloproject.com/schemas/contact_detail.json#"
    contact_details = GenericRelation(
        "ContactDetail", help_text="Means of contacting the organization"
    )

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = GenericRelation(
        "Link", help_text="URLs to documents about the organization"
    )

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    sources = GenericRelation(
        "Source", help_text="URLs to source documents about the organization"
    )

    # Copied from OrganizationExtra
    slug = models.CharField(max_length=256, blank=True, unique=True)
    register = models.CharField(blank=True, max_length=512)
    images = GenericRelation("images.Image")

    def ec_id(self):
        if self.classification != "Party":
            raise ValueError("'{}' isn't a Party".format(str(self)))
        try:
            party_id = self.identifiers.filter(
                scheme="electoral-commission"
            ).first()
            return party_id.identifier
        except:
            return "ynmp-party:2"

    try:
        # PassTrhroughManager was removed in django-model-utils 2.4, see issue #22
        objects = PassThroughManager.for_queryset_class(OrganizationQuerySet)()
    except:
        objects = OrganizationQuerySet.as_manager()

    def add_member(self, person):
        m = Membership(organization=self, person=person)
        m.save()

    def add_members(self, persons):
        for p in persons:
            self.add_member(p)

    def add_post(self, **kwargs):
        kwargs["slug"] = slugify(kwargs["label"])
        p = Post(organization=self, **kwargs)
        p.save()

    def add_posts(self, posts):
        for p in posts:
            self.add_post(**p)

    def __str__(self):
        return self.name


class Post(Dateframeable, Timestampable, models.Model):
    """
    A position that exists independent of the person holding it
    see schema at http://popoloproject.com/schemas/json#
    """

    label = models.CharField(
        _("label"),
        max_length=512,
        blank=True,
        help_text=_("A label describing the post"),
    )
    other_label = models.CharField(
        _("other label"),
        max_length=512,
        blank=True,
        null=True,
        help_text=_("An alternate label, such as an abbreviation"),
    )

    role = models.CharField(
        _("role"),
        max_length=512,
        blank=True,
        help_text=_("The function that the holder of the post fulfills"),
    )

    # reference to "http://popoloproject.com/schemas/organization.json#"
    organization = models.ForeignKey(
        "Organization",
        related_name="posts",
        help_text=_("The organization in which the post is held"),
    )

    # reference to "http://popoloproject.com/schemas/area.json#"
    area = models.ForeignKey(
        "Area",
        blank=True,
        null=True,
        related_name="posts",
        help_text=_("The geographic area to which the post is related"),
    )

    # array of items referencing "http://popoloproject.com/schemas/contact_detail.json#"
    contact_details = GenericRelation(
        "ContactDetail", help_text="Means of contacting the holder of the post"
    )

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = GenericRelation(
        "Link", help_text="URLs to documents about the post"
    )

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    sources = GenericRelation(
        "Source", help_text="URLs to source documents about the post"
    )

    # PostExtra fields
    slug = models.CharField(max_length=256, blank=True, unique=True)

    elections = models.ManyToManyField(
        "elections.Election",
        related_name="posts",
        through="candidates.PostExtraElection",
    )
    group = models.CharField(max_length=1024, blank=True)
    party_set = models.ForeignKey("candidates.PartySet", blank=True, null=True)

    @property
    def short_label(self):
        from candidates.election_specific import shorten_post_label

        return shorten_post_label(self.label)

    try:
        # PassTrhroughManager was removed in django-model-utils 2.4, see issue #22
        objects = PassThroughManager.for_queryset_class(PostQuerySet)()
    except:
        objects = PostQuerySet.as_manager()

    def __str__(self):
        return self.label


class Membership(Dateframeable, Timestampable, models.Model):
    """
    A relationship between a person and an organization
    see schema at http://popoloproject.com/schemas/membership.json#
    """

    label = models.CharField(
        _("label"),
        max_length=512,
        blank=True,
        help_text=_("A label describing the membership"),
    )
    role = models.CharField(
        _("role"),
        max_length=512,
        blank=True,
        help_text=_("The role that the person fulfills in the organization"),
    )

    # reference to "http://popoloproject.com/schemas/person.json#"
    person = models.ForeignKey(
        "Person",
        to_field="id",
        related_name="memberships",
        help_text=_("The person who is a party to the relationship"),
    )

    party = models.ForeignKey(
        "parties.Party",
        null=True,
        help_text="The political party for this membership",
        on_delete=models.PROTECT,
    )

    # reference to "http://popoloproject.com/schemas/post.json#"
    post = models.ForeignKey(
        "Post",
        blank=True,
        null=True,
        related_name="memberships",
        help_text=_(
            "The post held by the person in the organization through this membership"
        ),
    )

    # reference to "http://popoloproject.com/schemas/area.json#"
    area = models.ForeignKey(
        "Area",
        blank=True,
        null=True,
        related_name="memberships",
        help_text=_("The geographic area to which the post is related"),
    )

    # array of items referencing "http://popoloproject.com/schemas/contact_detail.json#"
    contact_details = GenericRelation(
        "ContactDetail",
        help_text="Means of contacting the member of the organization",
    )

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = GenericRelation(
        "Link", help_text="URLs to documents about the membership"
    )

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    sources = GenericRelation(
        "Source", help_text="URLs to source documents about the membership"
    )

    # Moved from MembeshipExtra
    elected = models.NullBooleanField()
    party_list_position = models.IntegerField(null=True)
    post_election = models.ForeignKey("candidates.PostExtraElection")

    def save(self, *args, **kwargs):
        if self.post_election and getattr(self, "check_for_broken", True):
            if self.post_election.election in self.person.not_standing.all():
                msg = "Trying to add a Membership with an election " '"{election}", but that\'s in {person} ' "({person_id})'s not_standing list."
                raise Exception(
                    msg.format(
                        election=self.post_election.election,
                        person=self.person.name,
                        person_id=self.person.id,
                    )
                )
        super().save(*args, **kwargs)

    try:
        # PassTrhroughManager was removed in django-model-utils 2.4, see issue #22
        objects = PassThroughManager.for_queryset_class(MembershipQuerySet)()
    except:
        objects = MembershipQuerySet.as_manager()

    def __str__(self):
        return self.label

    class Meta:
        unique_together = ("person", "post_election")


class ContactDetail(
    Timestampable, Dateframeable, GenericRelatable, models.Model
):
    """
    A means of contacting an entity
    see schema at http://popoloproject.com/schemas/contact-detail.json#
    """

    CONTACT_TYPES = Choices(
        ("ADDRESS", "address", _("Address")),
        ("EMAIL", "email", _("Email")),
        ("URL", "url", _("Url")),
        ("MAIL", "mail", _("Snail mail")),
        ("TWITTER", "twitter", _("Twitter")),
        ("FACEBOOK", "facebook", _("Facebook")),
        ("PHONE", "phone", _("Telephone")),
        ("MOBILE", "mobile", _("Mobile")),
        ("TEXT", "text", _("Text")),
        ("VOICE", "voice", _("Voice")),
        ("FAX", "fax", _("Fax")),
        ("CELL", "cell", _("Cell")),
        ("VIDEO", "video", _("Video")),
        ("PAGER", "pager", _("Pager")),
        ("TEXTPHONE", "textphone", _("Textphone")),
    )

    label = models.CharField(
        _("label"),
        max_length=512,
        blank=True,
        help_text=_("A human-readable label for the contact detail"),
    )
    contact_type = models.CharField(
        _("type"),
        max_length=12,
        choices=CONTACT_TYPES,
        help_text=_("A type of medium, e.g. 'fax' or 'email'"),
    )
    value = models.CharField(
        _("value"),
        max_length=512,
        help_text=_("A value, e.g. a phone number or email address"),
    )
    note = models.CharField(
        _("note"),
        max_length=512,
        blank=True,
        help_text=_(
            "A note, e.g. for grouping contact details by physical location"
        ),
    )

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    sources = GenericRelation(
        "Source", help_text="URLs to source documents about the contact detail"
    )

    try:
        # PassTrhroughManager was removed in django-model-utils 2.4, see issue #22
        objects = PassThroughManager.for_queryset_class(ContactDetailQuerySet)()
    except:
        objects = ContactDetailQuerySet.as_manager()

    def __str__(self):
        return u"{} - {}".format(self.value, self.contact_type)


class OtherName(Dateframeable, GenericRelatable, models.Model):
    """
    An alternate or former name
    see schema at http://popoloproject.com/schemas/name-component.json#
    """

    name = models.CharField(
        _("name"), max_length=512, help_text=_("An alternate or former name")
    )
    note = models.CharField(
        _("note"),
        max_length=1024,
        blank=True,
        help_text=_("A note, e.g. 'Birth name'"),
    )

    try:
        # PassTrhroughManager was removed in django-model-utils 2.4, see issue #22
        objects = PassThroughManager.for_queryset_class(OtherNameQuerySet)()
    except:
        objects = OtherNameQuerySet.as_manager()

    def __str__(self):
        return self.name


class Identifier(GenericRelatable, models.Model):
    """
    An issued identifier
    see schema at http://popoloproject.com/schemas/identifier.json#
    """

    identifier = models.CharField(
        _("identifier"),
        max_length=512,
        help_text=_("An issued identifier, e.g. a DUNS number"),
    )
    scheme = models.CharField(
        _("scheme"),
        max_length=128,
        blank=True,
        help_text=_("An identifier scheme, e.g. DUNS"),
    )

    def __str__(self):
        return "{}: {}".format(self.scheme, self.identifier)


class Link(GenericRelatable, models.Model):
    """
    A URL
    see schema at http://popoloproject.com/schemas/link.json#
    """

    url = models.URLField(_("url"), max_length=350, help_text=_("A URL"))
    note = models.CharField(
        _("note"),
        max_length=512,
        blank=True,
        help_text=_("A note, e.g. 'Wikipedia page'"),
    )

    def __str__(self):
        return self.url


class Source(GenericRelatable, models.Model):
    """
    A URL for referring to sources of information
    see schema at http://popoloproject.com/schemas/link.json#
    """

    url = models.URLField(_("url"), help_text=_("A URL"))
    note = models.CharField(
        _("note"),
        max_length=512,
        blank=True,
        help_text=_("A note, e.g. 'Parliament website'"),
    )

    def __str__(self):
        return self.url


class Language(models.Model):
    """
    Maps languages, with names and 2-char iso 639-1 codes.
    Taken from http://dbpedia.org, using a sparql query
    """

    dbpedia_resource = models.CharField(
        max_length=255, help_text=_("DbPedia URI of the resource"), unique=True
    )
    iso639_1_code = models.CharField(max_length=2)
    name = models.CharField(
        max_length=128, help_text=_("English name of the language")
    )

    def __str__(self):
        return u"{} ({})".format(self.name, self.iso639_1_code)


class Area(GenericRelatable, Dateframeable, Timestampable, models.Model):
    """
    An area is a geographic area whose geometry may change over time.
    see schema at http://popoloproject.com/schemas/area.json#
    """

    name = models.CharField(
        _("name"), max_length=256, blank=True, help_text=_("A primary name")
    )
    identifier = models.CharField(
        _("identifier"),
        max_length=512,
        blank=True,
        help_text=_("An issued identifier"),
    )
    classification = models.CharField(
        _("identifier"),
        max_length=512,
        blank=True,
        help_text=_("An area category, e.g. city"),
    )

    # array of items referencing "http://popoloproject.com/schemas/identifier.json#"
    other_identifiers = GenericRelation(
        "Identifier",
        blank=True,
        null=True,
        help_text="Other issued identifiers (zip code, other useful codes, ...)",
    )

    # reference to "http://popoloproject.com/schemas/area.json#"
    parent = models.ForeignKey(
        "Area",
        blank=True,
        null=True,
        related_name="children",
        help_text=_("The area that contains this area"),
    )

    # geom property, as text (GeoJson, KML, GML)
    geom = models.TextField(
        _("geom"), null=True, blank=True, help_text=_("A geometry")
    )

    # inhabitants, can be useful for some queries
    inhabitants = models.IntegerField(
        _("inhabitants"),
        null=True,
        blank=True,
        help_text=_("The total number of inhabitants"),
    )

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    sources = GenericRelation(
        "Source",
        blank=True,
        null=True,
        help_text="URLs to source documents about the contact detail",
    )

    def __str__(self):
        return self.name


class AreaI18Name(models.Model):
    """
    Internationalized name for an Area.
    Contains references to language and area.
    """

    area = models.ForeignKey("Area", related_name="i18n_names")
    language = models.ForeignKey("Language")
    name = models.CharField(_("name"), max_length=255)

    def __str__(self):
        return "{} - {}".format(self.language, self.name)

    class Meta:
        verbose_name = "I18N Name"
        verbose_name_plural = "I18N Names"
        unique_together = ("area", "language", "name")


##
## signals
##

## copy founding and dissolution dates into start and end dates,
## so that Organization can extend the abstract Dateframeable behavior
## (it's way easier than dynamic field names)
@receiver(pre_save, sender=Organization)
def copy_organization_date_fields(sender, **kwargs):
    obj = kwargs["instance"]

    if obj.founding_date:
        obj.start_date = obj.founding_date
    if obj.dissolution_date:
        obj.end_date = obj.dissolution_date


## copy birth and death dates into start and end dates,
## so that Person can extend the abstract Dateframeable behavior
## (it's way easier than dynamic field names)
@receiver(pre_save, sender=Person)
def copy_person_date_fields(sender, **kwargs):
    obj = kwargs["instance"]

    if obj.birth_date:
        obj.start_date = obj.birth_date
    if obj.death_date:
        obj.end_date = obj.death_date


## all instances are validated before being saved
@receiver(pre_save, sender=Person)
@receiver(pre_save, sender=Organization)
@receiver(pre_save, sender=Post)
def validate_date_fields(sender, **kwargs):
    obj = kwargs["instance"]
    obj.full_clean()
