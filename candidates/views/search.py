from haystack.generic_views import SearchView


class PersonSearch(SearchView):
    results_per_page = 5
