from os.path import exists, join

from django.conf import settings
from django.views.generic import TemplateView

from elections.models import Election


class HelpAboutView(TemplateView):
    template_name = "candidates/about.html"


class HelpResultsView(TemplateView):
    template_name = "candidates/results.html"

    def results_file_exists(self, election_slug):
        if election_slug is None:
            suffix = "all"
        else:
            suffix = election_slug
        expected_file_location = join(
            settings.MEDIA_ROOT, "candidates-elected-{}.csv".format(suffix)
        )
        return exists(expected_file_location)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["all_results_exists"] = self.results_file_exists(None)

        context["grouped_elections"] = Election.group_and_order_elections()
        for era_data in context["grouped_elections"]:
            for date, elections in era_data["dates"].items():
                for role_data in elections:
                    for election_dict in role_data["elections"]:
                        election = election_dict["election"]
                        election_dict[
                            "results_file_exists"
                        ] = self.results_file_exists(election.slug)

        return context
