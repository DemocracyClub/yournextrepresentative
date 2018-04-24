from django.conf.urls import url
from django.views.decorators.cache import cache_page
from django.views.decorators.clickjacking import xframe_options_exempt

from . import views


urlpatterns = [
    url(
        r'^$',
        views.ResultsHomeView.as_view(),
        name='results-home'
    ),
]

