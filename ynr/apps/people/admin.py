from django import forms
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.views.generic import TemplateView
from sorl.thumbnail.admin.current import AdminImageWidget

from candidates.models import LoggedAction
from candidates.models.db import ActionType
from candidates.views.version_data import get_client_ip
from people.data_removal_helpers import DataRemover
from people.models import (
    EditLimitationStatuses,
    Person,
    PersonImage,
    PersonNameSynonym,
)
from popolo.models import Membership


class RemovePersonalDataView(TemplateView):
    template_name = "admin/people/person/remove_personal_data_confirm.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        person = Person.objects.get(pk=self.kwargs["object_id"])
        context["person"] = person
        context["title"] = "Remove personal data for {}".format(person.name)
        self.data_remover = DataRemover(person)
        context["data_remover"] = self.data_remover.collect()

        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        self.data_remover.remove()
        return HttpResponseRedirect(
            reverse(
                "admin:people_person_change",
                kwargs={"object_id": context["person"].pk},
            )
        )


class MembershipInline(admin.StackedInline):
    extra = 0
    model = Membership


class PersonImageInlineForm(forms.ModelForm):
    class Meta:
        model = PersonImage
        widgets = {"image": AdminImageWidget}

        fields = ("image", "is_primary")


class PersonImageInline(admin.TabularInline):
    extra = 0
    model = PersonImage
    form = PersonImageInlineForm
    fields = ("id", "image", "is_primary")


class PersonAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("name", "gender", "birth_date", "death_date")}),
        (
            "Biography",
            {"classes": ("collapse",), "fields": ("summary", "biography")},
        ),
        (
            "Honorifics",
            {
                "classes": ("collapse",),
                "fields": ("honorific_prefix", "honorific_suffix"),
            },
        ),
        (
            "Special Names",
            {
                "classes": ("collapse",),
                "fields": (
                    "family_name",
                    "given_name",
                    "additional_name",
                    "patronymic_name",
                    "sort_name",
                ),
            },
        ),
        (
            "Edit limitations",
            {"classes": ("collapse",), "fields": ("edit_limitations",)},
        ),
    )

    list_filter = ("edit_limitations",)
    inlines = [PersonImageInline]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/remove_personal_data/",
                self.admin_site.admin_view(RemovePersonalDataView.as_view()),
                name="remove_personal_data_view",
            )
        ]
        return custom_urls + urls

    def save_model(self, request, obj, form, change):
        if form.initial["edit_limitations"] != form["edit_limitations"].value():

            try:
                limitation = EditLimitationStatuses[
                    form["edit_limitations"].value()
                ].value
                message = "Changed edit limitations to '{}'".format(limitation)
            except KeyError:
                message = "Removed edit limitations"

            LoggedAction.objects.create(
                user=request.user,
                action_type=ActionType.CHANGE_EDIT_LIMITATIONS,
                ip_address=get_client_ip(request),
                person=obj,
                source=message,
            )

        super().save_model(request, obj, form, change)


class PersonNameSynonymAdmin(admin.ModelAdmin):
    search_fields = ("term", "synonym")
    list_display = ("term", "synonym")


admin.site.register(Person, PersonAdmin)
admin.site.register(PersonNameSynonym, PersonNameSynonymAdmin)
