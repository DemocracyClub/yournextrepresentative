from django.db import models
from django.utils import timezone
from django_extensions.db.models import TimeStampedModel
from django.contrib.postgres.fields import ArrayField

from .managers import PartyQuerySet


class Party(TimeStampedModel):
    """
    A UK political party

    The canonical source of these parties is The Electoral Commission, with
    some exceptions. In Law, candidate can *technically* stand for 2 or
    fewer parties (that is, 0, 1 or 2 parties).

    To save representing this in the data model (and all the complexities that
    would arise) we make three types of "pseudo-party" objects:

    1. "Independent" (standing for 0 parties) is given the ID "ynmp-party:2"
    2. Joint parties (candidate standing for two parties) are each given a
       pseudo-party. These parties are guesses at by looking at the descriptions
       in the source data. For example, a description might look like:

       "Labour and Co-operative Party (Joint Description with Labour Party)"

       If we detect "Joint Description with" (or similar) we make a new party
    3. "Speaker seeking re-election". The speaker of the House of Commons doesn't
        stand for a party, rather they are elected directly in to that role
        (sort of). This is given the ID "ynmp-party:12522"

    """

    ec_id = models.CharField(
        db_index=True,
        max_length=25,
        unique=True,
        verbose_name="Electoral Commission Idenfitier",
        help_text="""
            An ID issued by The Electoral Commission in their party register,
            with the exception of Democracy Club psuedo IDs for special parties
        """,
    )
    name = models.CharField(max_length=255, verbose_name="Party name")
    alternative_name = models.CharField(max_length=255, null=True)
    register = models.CharField(
        max_length=2,
        db_index=True,
        null=True,
        verbose_name="Party register",
        help_text="""
            Normally either `GB` or `NI` depending on the
            country the party is registered in. Pseudo-parties don't have a
            register, so this field is nullable.
        """,
    )
    status = models.CharField(
        db_index=True,
        max_length=255,
        verbose_name="Party registration status",
        choices=[
            ("Registered", "Registered"),
            ("Deregistered", "Deregistered"),
        ],
    )
    date_registered = models.DateField()
    date_deregistered = models.DateField(null=True)
    legacy_slug = models.CharField(
        max_length=256,
        blank=True,
        unique=True,
        help_text="""
            DEPRECATED: A slug used in URLs that comes from a previous way of modelling parties.
            This field will be removed in the future in favour of the `ec_id`.
            """,
    )
    current_candidates = models.PositiveSmallIntegerField(default=0)
    total_candidates = models.PositiveIntegerField(default=0)
    ec_data = models.JSONField(default=dict)
    nations = ArrayField(
        models.CharField(max_length=3),
        max_length=3,
        null=True,
        verbose_name="Party nations",
        help_text="""
                Some subset of ["ENG", "WAL", "SCO"],
                depending on where the party fields candidates. 
                Nullable as not applicable to NI-based parties.
            """,
    )

    objects = PartyQuerySet.as_manager()

    def __str__(self):
        return "{} ({})".format(self.name, self.ec_id)

    class Meta:
        ordering = ("name",)

    @property
    def default_emblem(self):
        """
        Parties can have `n` emblems, however there is typically one that is
        the "main" emblem. For example a party might have three emblems:
        "The Foo Party", "The Foo Party of Wales", "The Scottish Foo Party".


        When showing a single emblem without the context of a candidate, it's
        useful to have a shortcut to the most generic version of the party
        emblem.
        """
        return self.emblems.first()

    @property
    def as_slack_attachment(self):
        """
        Format this Party in a way that can be sent to `utils.slack.SlackHelper`

        :return:
        """

        url = "http://search.electoralcommission.org.uk/English/Registrations/{}".format(
            self.ec_id
        )
        attachment = {
            "title": self.name,
            "title_link": url,
            "fallback": "{} {}".format(self.name, url),
        }
        if self.default_emblem:
            attachment[
                "image_url"
            ] = "http://search.electoralcommission.org.uk/Api/Registrations/Emblems/{}".format(
                self.default_emblem.ec_emblem_id
            )
        if self.descriptions.exists():

            attachment["fields"] = [
                {
                    "title": "Descriptions",
                    "value": "\n".join(
                        [d.description for d in self.descriptions.all()]
                    ),
                    "short": False,
                }
            ]
        return attachment

    @property
    def is_deregistered(self):
        if not self.date_deregistered:
            return False
        return self.date_deregistered > timezone.now().date()

    @property
    def format_name(self):
        name = self.name
        if self.is_deregistered:
            name = "{} (Deregistered {})".format(name, self.date_deregistered)
        return name


class PartyDescription(TimeStampedModel):
    """
    A party can register one or more descriptions with The Electoral Commission.

    Each description can be used by a candidate on a ballot paper, along side
    their name and chosen emblem.
    """

    party = models.ForeignKey(
        Party, on_delete=models.CASCADE, related_name="descriptions"
    )

    description = models.CharField(max_length=800)
    date_description_approved = models.DateField(null=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-active"]


def emblem_upload_path(instance, filename):
    return "emblems/{}/{}_{}".format(
        instance.party.ec_id, instance.ec_emblem_id, filename
    )


class PartyEmblem(TimeStampedModel):
    """
    A Party can register emblems with The Electoral Commission.

    Candidates can pick of the the registered emblems to appear against their
    name on ballot papers.

    As a useful shortcut, we set a [default_emblem](#/definitions/Party/default_emblem)
    to indicate that this is the most generic emblem.

    """

    party = models.ForeignKey(
        Party, on_delete=models.CASCADE, related_name="emblems"
    )
    ec_emblem_id = models.PositiveIntegerField(primary_key=True)
    image = models.ImageField(upload_to=emblem_upload_path)
    description = models.CharField(max_length=255)
    date_approved = models.DateField(null=True)
    default = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ("-default", "-active", "ec_emblem_id")

    def __str__(self):
        return '{} ("{}")'.format(self.pk, self.description)
