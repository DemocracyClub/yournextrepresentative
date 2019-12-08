from django.conf.urls import url

from .feeds import BasicResultEventsFeed, ResultEventsFeed
from uk_results.views import Parl19ResultsCSVView

urlpatterns = [
    url(r"^all\.atom$", ResultEventsFeed(), name="atom-results"),
    url(
        r"^all-basic\.atom$", BasicResultEventsFeed(), name="atom-results-basic"
    ),
    url(
        r"^csv/parl.2019-12-12/$",
        Parl19ResultsCSVView.as_view(),
        name="parl-2019-csv-results",
    ),
]
