from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Count, F

from people.models import Person


def search_person_by_name(name, synonym=True):
    and_name = " & ".join(name.strip().split(" "))
    or_name = " | ".join(name.strip().split(" "))
    name = f"({and_name}) | ({or_name})"
    query = SearchQuery(name, search_type="raw", config="english")

    search_args = {}
    if synonym:
        search_args["name_search_vector__synonym"] = query
    else:
        search_args["name_search_vector"] = query

    qs = (
        Person.objects.annotate(membership_count=Count("memberships"))
        .filter(**search_args)
        .annotate(rank=SearchRank(F("name_search_vector"), query))
        .order_by("-rank", "membership_count")
        .defer("biography", "versions")
    )

    return qs
