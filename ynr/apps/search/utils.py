import operator
from functools import reduce

from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.db.models import Count

from people.models import Person


def or_term(term):
    terms = [SearchQuery(term_sq) for term_sq in term.split(" ")]
    if len(terms) == 1:
        return terms[0]
    return reduce(operator.or_, terms)


def search_person_by_name(name):
    vector = SearchVector("name")
    query = or_term(name)

    qs = (
        Person.objects
        # .values("person_id")
        .annotate(membership_count=Count("memberships"))
        .filter(name__search=query)
        .annotate(rank=SearchRank(vector, query))
        .order_by("-rank", "-membership_count")
        .defer("biography", "versions")
    )

    return qs
