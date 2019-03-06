from django.views.generic import DetailView, ListView
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count

from candidates.models import LoggedAction
from wombles.models import WombleTags


class SingleWombleView(LoginRequiredMixin, DetailView):
    template_name = "wombles/single_womble.html"
    model = User

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["edits_over_time"] = (
            LoggedAction.objects.filter(user=self.object)
            .extra({"day": "date_trunc('week', date(created))"})
            .values("day")
            .annotate(edits=Count("pk"))
            .values("day", "edits")
            .order_by("day")
        )

        context[
            "edits_over_time"
        ] = self.object.womble_profile.edits_over_time()
        return context


class WombleTagsView(LoginRequiredMixin, ListView):
    model = WombleTags


class WombleTagView(LoginRequiredMixin, DetailView):
    slug_url_kwarg = "tag"
    slug_field = "label"

    def get_queryset(self):
        return WombleTags.objects.all().prefetch_related(
            "wombleprofile_set__user",
            "wombleprofile_set__tags",
            "wombleprofile_set__user__loggedaction_set",
        )
