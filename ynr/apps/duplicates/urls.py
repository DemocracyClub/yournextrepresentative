from django.conf.urls import url

from .views import DuplicateSuggestionListView

urlpatterns = [
    url(r'^$',
        DuplicateSuggestionListView.as_view(),
        name="duplicate_list"),

]
