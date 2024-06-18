from django.urls import re_path
from django.views.generic import RedirectView

from .feeds import BasicResultEventsFeed, ResultEventsFeed

urlpatterns = [
    re_path(r"^all\.atom$", ResultEventsFeed(), name="atom-results"),
    re_path(
        r"^all-basic\.atom$", BasicResultEventsFeed(), name="atom-results-basic"
    ),
    re_path(
        r"^csv/parl.2019-12-12/$",
        RedirectView.as_view(
            url="/data/export_csv/?election_id=parl.2019-12-12&field_group=results"
        ),
        name="parl-2019-csv-results",
    ),
]
