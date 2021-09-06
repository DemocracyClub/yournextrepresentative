from django.urls import re_path

from .feeds import BasicResultEventsFeed, ResultEventsFeed
from uk_results.views import Parl19ResultsCSVView

urlpatterns = [
    re_path(r"^all\.atom$", ResultEventsFeed(), name="atom-results"),
    re_path(
        r"^all-basic\.atom$", BasicResultEventsFeed(), name="atom-results-basic"
    ),
    re_path(
        r"^csv/parl.2019-12-12/$",
        Parl19ResultsCSVView.as_view(),
        name="parl-2019-csv-results",
    ),
]
