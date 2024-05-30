from typing import List, Optional, TextIO

from data_exports.csv_fields import csv_fields, get_core_fieldnames
from django.db import connection, models, transaction
from django.db.models import Count, IntegerField, JSONField
from django.db.models.expressions import Case, When
from django.db.models.functions import Coalesce
from utils.db import LastWord, NullIfBlank
from ynr_refactoring.settings import PersonIdentifierFields


class MaterializedModelMixin:
    @classmethod
    @transaction.atomic
    def refresh_view(cls):
        with connection.cursor() as cursor:
            cursor.execute(
                "REFRESH MATERIALIZED VIEW {}".format(cls._meta.db_table)
            )


class MaterializedMembershipsQuerySet(models.QuerySet):
    def _fieldnames(self, extra_fields: Optional[List] = None):
        fieldnames = get_core_fieldnames()
        if extra_fields:
            fieldnames += extra_fields
        return fieldnames

    def _with_fields(self, extra_fields: Optional[List] = None):
        fieldnames = self._fieldnames(extra_fields)
        qs = self.select_related(
            "ballot_paper", "party", "person", "ballot_paper__election"
        )

        for name in fieldnames:
            field = csv_fields[name]
            if field.type == "expr":
                qs = qs.annotate(**{name: field.value})
        qs = qs.values().values(*fieldnames)
        return qs.order_by(
            "election_date",
            "ballot_paper_id",
            Coalesce(
                NullIfBlank("person__sort_name"),
                LastWord("person__name"),
            ),
        )

    def for_data_table(self, extra_fields: Optional[List] = None):
        self._fieldnames(extra_fields)
        return self._with_fields(extra_fields)

    def write_csv(self, file_like: TextIO, extra_fields: Optional[List] = None):
        """
        Asks Postgres to make a CSV for us, rather than using Django/Python to do it.

        The simple way to make a CSV from a QuerySet would be to use the builtin
        `csv` library and iterate over a Django QuerySet.

        This works, but each row in the CSV is turned into a Django Model object first
        and then a Python dict object before being converted to a CSV line.

        This is memory expensive, and that matters when we have a large number of rows.

        Rather, we use PostgreSQL's ability to SELECT AS CSV. This means Postgres does almost
        the exact same amount of work as just selecting the rows for Django, but Django and Python
        have nothing to do.

        To do this we need to break out of the ORM and use `copy_expert`. This
        comes with a couple of tricky elements:

        1. We use `qs.query.sql_with_params()` to get underlying the ORM query. This means we
           don't have to manage the main SQL manually.
        2. Django's ORM doesn't really care about the order of SELECTed fields, as it's intended
           to always convert them to models. `values_list` is the closest, but even that
           does the ordering when converting to a Python list, not in the SQL.
           Because we use SELECT...AS CSV, the column ordering converts into the CSV column
           order. To ensure the orders can be controlled we wrap the ORM query in an outer
           query that selects the fields in the same order as the selected fields.

        :param file_like: a file-like object that copy_expert can write to
        :param extra_fields: exrta headers defined in `csv_fields` to add to the CSV
            (core headers always included)


        """
        fieldnames = self._fieldnames(extra_fields)
        sql, params = self.query.sql_with_params()
        fields = [f"QS.{field}" for field in fieldnames]

        outer_query = f"""select {", ".join(fields)} FROM ({sql}) as QS"""
        sql = f"COPY ({outer_query}) TO STDOUT WITH (FORMAT CSV, HEADER)"

        with connection.cursor() as cur:
            sql = cur.mogrify(sql, params)
            with cur.copy(sql) as copy:
                for row in copy:
                    file_like.write(row)

    def percentage_for_fields(self):
        identifier_fields = sorted(pi.name for pi in PersonIdentifierFields)
        total_rows = self.count()
        annotations = {}
        for field in identifier_fields:
            annotations[field] = Count(
                Case(
                    When(**{f"identifiers__{field}__isnull": False}, then=1),
                    output_field=IntegerField(),
                )
            )

        results = self.aggregate(**annotations)
        ret = {}
        for field, count in results.items():
            if not count:
                ret[field] = 0
                continue
            ret[field] = (count / total_rows) * 100
        return ret


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
