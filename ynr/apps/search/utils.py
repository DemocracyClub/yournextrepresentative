from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Count, F

from people.models import Person


def search_person_by_name(name):
    name = " | ".join(name.split(" "))
    query = SearchQuery(name, search_type="raw")

    qs = (
        Person.objects.annotate(membership_count=Count("memberships"))
        .filter(name_search_vector=query)
        .annotate(rank=SearchRank(F("name_search_vector"), query))
        .order_by("rank", "membership_count")
        .defer("biography", "versions")
    )

    return qs
