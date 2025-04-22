from candidates.models import Ballot
from django.contrib import admin

from .models import ResultEvent


class ResultEventAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "election",
        "user",
        "created",
        "winner_link",
        "old_post_id",
        "old_post_name",
        "election_link",
        "source",
    )
    search_fields = (
        "id",
        "election__name",
        "user__username",
        "winner__name",
        "old_post_id",
        "old_post_name",
        "source",
    )
    ordering = ("-created",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "user", "winner", "post", "winner_party", "election"
        )

    def winner_link(self, o):
        return o.winner.get_absolute_url()

    def election_link(self, o):
        if o.post:
            ballot = Ballot.objects.get(election=o.election, post=o.post)
            return ballot.get_absolute_url()
        # There is still data in the database for some posts that
        # were deleted and never recreated, so we can't create a
        # link for them.
        return ""


admin.site.register(ResultEvent, ResultEventAdmin)
