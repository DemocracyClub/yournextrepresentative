from django.db import connection, models, transaction
from django.db.models import JSONField


class MaterializedModelMixin:
    @classmethod
    @transaction.atomic
    def refresh_view(cls):
        with connection.cursor() as cursor:
            cursor.execute(
                "REFRESH MATERIALIZED VIEW {}".format(cls._meta.db_table)
            )


class MaterializedMembershipsQuerySet(models.QuerySet):
    def for_csv(self):
        qs = self.select_related(
            "ballot_paper", "party", "person", "ballot_paper__election"
        )
        return qs.order_by("election_date", "ballot_paper_id", "last_name")


class MaterializedMemberships(MaterializedModelMixin, models.Model):
    """
    This model isn't managed by Django, as it's a PostgreSQL "materialized view".

    https://en.wikipedia.org/wiki/Materialized_view

    Rather than a table, it's a query that's run once and then the results are stored in the database.

    The view is created in a migration like a normal Django model, but the migration is running
    raw SQL. We then make an unmanaged model in Django (See Meta.managed = False) that can be
    used like a normal Django model.

    Every field that's added here needs to be added via a new migration, and every change to the view
    made in a migrations needs to be reflected here for Django to know about it.

    """

    class Meta:
        db_table = "materialized_memberships"
        managed = False
        ordering = (
            "election_date",
            "ballot_paper_id",
        )

    membership = models.OneToOneField(
        "popolo.Membership",
        db_column="id",
        primary_key=True,
        on_delete=models.DO_NOTHING,
    )
    ballot_paper = models.ForeignKey(
        "candidates.Ballot",
        to_field="ballot_paper_id",
        on_delete=models.DO_NOTHING,
    )
    is_by_election = models.BooleanField()
    party = models.ForeignKey(
        "parties.Party", to_field="ec_id", on_delete=models.DO_NOTHING
    )
    party_name = models.CharField(max_length=800)
    party_list_position = models.PositiveIntegerField()
    person = models.ForeignKey("people.Person", on_delete=models.DO_NOTHING)
    person_name = models.CharField(max_length=800)

    election_name = models.CharField(max_length=800)
    election_date = models.DateField()
    division_name = models.CharField(max_length=800)

    elected = models.BooleanField()
    identifiers = JSONField()

    objects = MaterializedMembershipsQuerySet.as_manager()
