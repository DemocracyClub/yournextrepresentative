import re
import unicodedata

from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db import connection
from django.db.models import Count, F, OuterRef, Subquery
from people.managers import PersonQuerySet
from people.models import Person
from popolo.models import Membership


def search_person_by_name(name: str, synonym: bool = False) -> PersonQuerySet:
    """
    Take a string and turn it into a Django query that uses PostgresSQLs full
    text search.

    This function manages query parsing, and prevents the user passing in
    search logic.

    The complexity arises because we use a synonyms table for common name
    synonyms. This is done using PostgresSQLs built in `ts_rewrite`, however
    see the comment in line about a workaround for a performance bug.

    """
    name = (
        unicodedata.normalize("NFKD", name)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    name = name.lower()
    name = re.sub(r"[^a-z ]", " ", name)
    name = " ".join(name.strip().split())
    if not name:
        return Person.objects.none()
    and_name = " & ".join(name.split(" "))
    or_name = " | ".join(name.split(" "))
    name = f"({and_name}) | ({or_name})"
    name = name.strip()

    if synonym:
        # First perform a query that builts the final query
        # We do this because of a bug in Postgres and `ts_rewrite`.
        # In theory we can use `ts_rewrite` in line, however this causes the
        # search query to take almost 10 seconds on the full database.
        # Doing the rewrite to add synonnyms first and then passing that query
        # in to the actual search speeds this up, with the final search taking
        # less than 30ms
        with connection.cursor() as cursor:
            # This query takes the search terms and returns a query string
            # with name synonyms attached.
            # For example with:
            # ```
            # PersonNameSynonym.objects.create(term="sam", synonym="samantha")
            # ```
            # The search for "sam" would be transformed in to "(sam | samantha)"
            # with `|` acting as an OR operator
            cursor.execute(
                """
            SELECT ts_rewrite(
                to_tsquery('simple'::regconfig, %s),
                'SELECT term, synonym
                FROM people_personnamesynonym
                WHERE to_tsquery(''simple''::regconfig, '%s') @> term'
            );
            """,
                (name, name),
            )
            row = cursor.fetchone()

        query = SearchQuery(row[0], search_type="raw", config="simple")
    else:
        query = SearchQuery(name, search_type="raw", config="simple")

    # Build the query
    membership_subquery = Subquery(
        Membership.objects.filter(person=OuterRef("id"))
        .order_by("-pk")
        .values("party_name")[:1]
    )
    return (
        Person.objects.annotate(membership_count=Count("memberships"))
        .filter(name_search_vector=query)
        .annotate(vector=F("name_search_vector"))
        .annotate(party_name=membership_subquery)
        .annotate(
            rank=SearchRank(
                F("vector"),
                query,
                cover_density=True,
                weights=[0.1, 0.3, 0.4, 1],
            )
        )
        .select_related("image")
        .order_by("-rank", "membership_count")
        .defer("biography", "versions")
    )
