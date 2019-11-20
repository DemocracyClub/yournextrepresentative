from django import forms
from django.contrib import admin
from sorl.thumbnail.admin.current import AdminImageWidget

from candidates.models import LoggedAction
from candidates.views.version_data import get_client_ip
from people.models import EditLimitationStatuses, Person, PersonImage
from popolo.models import Membership


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
                action_type="change-edit-limitations",
                ip_address=get_client_ip(request),
                person=obj,
                source=message,
            )

        super().save_model(request, obj, form, change)


admin.site.register(Person, PersonAdmin)
