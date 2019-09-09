from django.contrib import admin
from django import forms

from sorl.thumbnail.admin.current import AdminImageWidget

from popolo.models import Membership
from people.models import Person, PersonImage


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
    fields = ("image", "is_primary")


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


admin.site.register(Person, PersonAdmin)
