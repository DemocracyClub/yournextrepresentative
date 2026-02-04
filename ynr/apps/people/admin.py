from candidates.models import LoggedAction
from candidates.models.db import ActionType
from candidates.views.version_data import get_client_ip
from django import forms
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.utils.html import format_html, mark_safe
from django.views.generic import TemplateView
from people.data_removal_helpers import DataRemover
from people.models import (
    EditLimitationStatuses,
    Person,
    PersonImage,
    PersonNameSynonym,
)
from popolo.admin import MembershipAdminForm
from popolo.models import Membership
from sorl.thumbnail.admin.current import AdminImageWidget


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
    form = MembershipAdminForm
    extra = 0
    can_delete = False
    model = Membership
    fields = (
        "admin_link",
        "party",
        "get_ballot",
        "deselected",
        "deselected_source",
    )
    readonly_fields = ("admin_link", "party", "get_ballot")

    @admin.display(description="Ballot")
    def get_ballot(self, obj):
        return obj.ballot.ballot_paper_id

    @admin.display(description="Membership object")
    def admin_link(self, obj):
        if not obj.pk:
            return "-"
        url = reverse(
            "admin:popolo_membership_change",
            args=[obj.pk],
        )
        return format_html('<a href="{}">Open</a>', url)

    def has_add_permission(self, request, obj=None):
        return False


class PersonImageInlineForm(forms.ModelForm):
    class Meta:
        model = PersonImage
        widgets = {"image": AdminImageWidget}

        fields = ("image",)


class PersonImageInline(admin.TabularInline):
    extra = 0
    model = PersonImage
    form = PersonImageInlineForm
    fields = ("id", "image")


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
            "Restrictions",
            {
                "classes": ("collapse",),
                "fields": ("edit_limitations", "delisted"),
            },
        ),
    )

    list_filter = ("edit_limitations",)
    list_display = (
        "name",
        "image_preview",
        "image_filetype",
    )
    inlines = [PersonImageInline, MembershipInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("image")

    def has_delete_permission(self, request, obj=None):
        return False

    def image_preview(self, obj):
        image_url = mark_safe(
            '<img src="/media/{}" width="50" height="50" />'.format(
                obj.image.image.name
            )
        )
        if obj.image:
            return image_url
        return "No Image Found"

    def image_filetype(self, obj):
        if obj.image:
            return obj.image.image.name.split(".")[-1]
        return "No Image Found"

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


class PersonImageAdmin(admin.ModelAdmin):
    model = PersonImage
    list_display = ("person", "image", "id", "is_primary")
    list_filter = ("is_primary",)
    fields = ("id", "image", "is_primary", "person")


class PersonNameSynonymAdmin(admin.ModelAdmin):
    search_fields = ("term", "synonym")
    list_display = ("term", "synonym")


admin.site.register(Person, PersonAdmin)
admin.site.register(PersonNameSynonym, PersonNameSynonymAdmin)
