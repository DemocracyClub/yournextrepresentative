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


@admin.register(Ballot)
class BallotAdmin(admin.ModelAdmin):
    list_display = ["post", "election", "winner_count"]
    list_filter = ("election__name", "election__current")
    raw_id_fields = ("post", "election")

    ordering = ("election", "post__label")
