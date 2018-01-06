# If you need to define any views specific to this country's site, put
# those definitions here.

from __future__ import unicode_literals

from django.views.generic import FormView

from candidates.views.mixins import ContributorsMixin
from elections.uk.forms import PostcodeForm


class HomePageView(ContributorsMixin, FormView):
    template_name = 'candidates/finder.html'
    form_class = PostcodeForm
