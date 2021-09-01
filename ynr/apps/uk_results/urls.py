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
        r"^(?P<ballot_paper_id>[^/]+)/",
        views.BallotPaperResultsUpdateView.as_view(),
        name="ballot_paper_results_form",
    ),
]
