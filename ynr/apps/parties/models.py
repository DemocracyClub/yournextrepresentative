from django.db import models

from django_extensions.db.models import TimeStampedModel

from .managers import PartyQuerySet


class Party(TimeStampedModel):
    """
    A UK political party

    The canonical source of these parties is The Electoral Commission, with
    some exceptions. Candidate can _technically_ stand for 2 or fewer parties
    (that is, 0, 1 or 2 parties). To save representing this in the data model
    (and all the complexities that would arise) we make three types of
    "psudo-party" objects:

    1. "Independent" (standing for 0 parties) is given the ID "ynmp-party:2"
    2. Join parties (candidate standing for two parties) are each given a
       psudo-party. These parties are guesses at by looking at the descriptions
       in the source data. For example, a description might look like:

       "Labour and Co-operative Party (Joint Description with Labour Party)"

       If we detect "Joint Description with" (or similar) we make a new party
    3. "Speaker seeking re-election". The speaker of the house doens't
        stand for a party, rather they are elected directly in to that role
        (sort of). Thisis given the ID "ynmp-party:12522"


    """

    ec_id = models.CharField(db_index=True, max_length=20)
    name = models.CharField(max_length=255)
    register = models.CharField(max_length=2, db_index=True, null=True)
    status = models.CharField(db_index=True, max_length=255)
    date_registered = models.DateField()
    date_deregistered = models.DateField(null=True)
    legacy_slug = models.CharField(max_length=256, blank=True, unique=True)

    objects = PartyQuerySet.as_manager()

    def __str__(self):
        return "{} ({})".format(self.name, self.ec_id)

    class Meta:
        ordering = ("name",)

    @property
    def default_emblem(self):
        return self.emblems.first()


class PartyDescription(TimeStampedModel):
    party = models.ForeignKey(
        Party, on_delete=models.CASCADE, related_name="descriptions"
    )

    description = models.CharField(max_length=800)
    date_description_approved = models.DateField(null=True)


def emblem_upload_path(instance, filename):
    return "emblems/{}/{}_{}".format(
        instance.party.ec_id, instance.ec_emblem_id, filename
    )


class PartyEmblem(TimeStampedModel):
    party = models.ForeignKey(
        Party, on_delete=models.CASCADE, related_name="emblems"
    )
    ec_emblem_id = models.IntegerField(primary_key=True)
    image = models.ImageField(upload_to=emblem_upload_path)
    description = models.CharField(max_length=255)
    date_approved = models.DateField(null=True)
    default = models.BooleanField(default=False)

    class Meta:
        ordering = ("-default", "ec_emblem_id")

    def __str__(self):
        return '{} ("{}")'.format(self.pk, self.description)
