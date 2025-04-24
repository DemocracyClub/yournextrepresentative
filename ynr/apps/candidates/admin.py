from django.contrib import admin
from django.forms import ModelForm
from django.urls import reverse

from .models import Ballot, LoggedAction, PartySet


class LoggedActionAdminForm(ModelForm):
    pass


@admin.register(LoggedAction)
class LoggedActionAdmin(admin.ModelAdmin):
    form = LoggedActionAdminForm
    search_fields = (
        "user__username",
        "popit_person_new_version",
        "person__name",
        "ip_address",
        "source",
    )
    list_filter = ("action_type",)
    list_display = [
        "user",
        "ip_address",
        "action_type",
        "popit_person_new_version",
        "person_link",
        "created",
        "updated",
        "source",
    ]
    ordering = ("-created",)

    def person_link(self, o):
        if not o.person:
            return ""
        url = reverse("person-view", kwargs={"person_id": o.person.id})
        return '<a href="{}">{}</a>'.format(url, o.person.name)

    person_link.allow_tags = True


class PartySetAdminForm(ModelForm):
    pass


@admin.register(PartySet)
class PartySetAdmin(admin.ModelAdmin):
    form = PartySetAdminForm


class ElectionTypeFilter(admin.SimpleListFilter):
    title = "Election type"
    parameter_name = "election_type"

    def lookups(self, request, model_admin):
        qs = model_admin.model.objects.values_list("ballot_paper_id", flat=True)
        types = sorted({val.split(".", 1)[0] for val in qs if val})
        return [(t, t) for t in types]

    def queryset(self, request, queryset):
        if self.value():
            # filter records whose field starts with e.g. "local."
            return queryset.filter(
                ballot_paper_id__startswith=f"{self.value()}."
            )
        return queryset


@admin.register(Ballot)
class BallotAdmin(admin.ModelAdmin):
    search_fields = ("ballot_paper_id",)
    date_hierarchy = "election__election_date"
    list_display = [
        "ballot_paper_id",
        "post",
        "election",
        "list_display_election_date",
        "winner_count",
    ]
    list_filter = (
        "election__current",
        ElectionTypeFilter,
    )
    raw_id_fields = ("post", "election", "replaces")
    readonly_fields = ("ee_modified", "ballot_paper_id")

    ordering = ("election", "post__label")

    def list_display_election_date(self, obj):
        return obj.election.election_date
