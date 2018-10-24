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

from slugify import slugify

from django.core.validators import RegexValidator
from django.db import models
from model_utils import Choices
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import pre_save
from django.dispatch import receiver

from candidates.models import ComplexPopoloField, PersonExtraFieldValue

from .behaviors.models import Timestampable, Dateframeable, GenericRelatable
from .querysets import (
    PostQuerySet,
    OtherNameQuerySet,
    ContactDetailQuerySet,
    MembershipQuerySet,
    OrganizationQuerySet,
)


class MultipleTwitterIdentifiers(Exception):
    pass


class VersionNotFound(Exception):
    pass


class Organization(Dateframeable, Timestampable, models.Model):
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
        "people.Person",
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
                msg = (
                    "Trying to add a Membership with an election "
                    '"{election}", but that\'s in {person} '
                    "({person_id})'s not_standing list."
                )
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


## all instances are validated before being saved
# @receiver(pre_save, sender=Person)
@receiver(pre_save, sender=Organization)
@receiver(pre_save, sender=Post)
def validate_date_fields(sender, **kwargs):
    obj = kwargs["instance"]
    obj.full_clean()
