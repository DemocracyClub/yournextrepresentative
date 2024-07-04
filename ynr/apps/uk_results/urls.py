from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^$", views.ResultsHomeView.as_view(), name="results-home"),
    re_path(
        r"^no-results/$",
        views.CurrentElectionsWithNoResuts.as_view(),
        name="current-elections-with-no-resuts",
    ),
    re_path(
        r"parl.2024-07-04/",
        views.ParlBallotsWinnerEntryView.as_view(),
        name="parl_24_winner_form",
    ),
    re_path(
        r"^(?P<ballot_paper_id>[^/]+)/",
        views.BallotPaperResultsUpdateView.as_view(),
        name="ballot_paper_results_form",
    ),
]
