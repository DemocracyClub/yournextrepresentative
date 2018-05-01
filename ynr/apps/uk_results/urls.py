from django.conf.urls import url

from . import views

urlpatterns = [
    url(
        r'^$',
        views.ResultsHomeView.as_view(),
        name='results-home'
    ),
    url(
        r'^(?P<ballot_paper_id>[^/]+)/',
        views.BallotPaperResultsUpdateView.as_view(),
        name='ballot_paper_results_form'
    ),

]
