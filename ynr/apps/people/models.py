import json
from datetime import date

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import models
from django.template import loader
from django.templatetags.static import static
from django.utils.functional import cached_property
from django.utils.six import text_type
from django.utils.six.moves.urllib_parse import quote_plus, urljoin
from django.utils.translation import ugettext_lazy as _
from popolo.behaviors.models import GenericRelatable, Timestampable
from popolo.models import (
    ComplexPopoloField,
    ContactDetail,
    Identifier,
    Membership,
    MultipleTwitterIdentifiers,
    PersonExtraFieldValue,
    VersionNotFound,
)
from slugify import slugify
from sorl.thumbnail import get_thumbnail

from candidates.diffs import get_version_diffs
from people.managers import PersonImageManager, PersonQuerySet


def person_image_path(instance, filename):
    # Ensure the filename isn't too long
    filename = filename[400:]
    # Upload images in a directory per person
    return "images/people/{0}/{1}".format(instance.person.id, filename)


class PersonImage(models.Model):
    """
    Images of people, uploaded by users of the site. It's important we keep
    track of the copyright the uploading user asserts over the image, and any
    notes they have.
    """

    person = models.ForeignKey("people.Person", related_name="images")
    image = models.ImageField(upload_to=person_image_path, max_length=512)
    source = models.CharField(max_length=400)
    copyright = models.CharField(max_length=64, default="other", blank=True)
    uploading_user = models.ForeignKey("auth.User", blank=True, null=True)
    user_notes = models.TextField(blank=True)
    md5sum = models.CharField(max_length=32, blank=True)
    user_copyright = models.CharField(max_length=128, blank=True)
    notes = models.TextField(blank=True)
    is_primary = models.BooleanField(default=False)

    objects = PersonImageManager()


class Person(Timestampable, models.Model):
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
        "popolo.OtherName", help_text="Alternate or former names"
    )

    # array of items referencing "http://popoloproject.com/schemas/identifier.json#"
    identifiers = GenericRelation(
        "popolo.Identifier", help_text="Issued identifiers"
    )

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
        "popolo.ContactDetail", help_text="Means of contacting the person"
    )

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    links = GenericRelation(
        "popolo.Link", help_text="URLs to documents related to the person"
    )

    # array of items referencing "http://popoloproject.com/schemas/link.json#"
    sources = GenericRelation(
        "popolo.Source", help_text="URLs to source documents about the person"
    )

    # Former 'extra' fields
    # This field stores JSON data with previous version information
    # (as it did in PopIt).
    versions = models.TextField(blank=True)
    not_standing = models.ManyToManyField(
        "elections.Election", related_name="persons_not_standing_tmp"
    )

    class Meta:
        verbose_name_plural = "People"

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
        from people.helpers import parse_approximate_date

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
        from people.helpers import squash_whitespace

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
        from people.helpers import update_person_from_form

        update_person_from_form(self, form)

    @classmethod
    def create_from_form(cls, form):
        from people.helpers import update_person_from_form

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
                    image_copyright = primary_image.copyright
                    user = primary_image.uploading_user
                    if user is not None:
                        image_uploading_user = (
                            primary_image.uploading_user.username
                        )
                    image_uploading_user_notes = primary_image.user_notes
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

    @property
    def primary_image(self):
        images = self.images.filter(is_primary=True)
        if images.exists():
            return images.first().image

    def get_display_image_url(self):
        """
        Return either the person's primary image or blank outline of a person
        """

        if self.primary_image:
            return get_thumbnail(self.primary_image.file, "x64").url

        return static("candidates/img/blank-person.png")

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
