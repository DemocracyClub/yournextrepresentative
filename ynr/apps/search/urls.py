from django.urls import path

from search.views import PersonSearch

urlpatterns = [path("search", PersonSearch.as_view(), name="person-search")]
