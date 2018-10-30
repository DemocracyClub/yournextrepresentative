from django.contrib import admin
from django.forms import ModelForm

from candidates.models import (
    ComplexPopoloField,
    PersonExtraFieldValue,
    ExtraField,
)
from popolo.models import Membership
from people.models import Person


class MembershipInline(admin.StackedInline):
    extra = 0
    model = Membership


class PersonAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("name", "gender", "birth_date", "death_date")}),
        (
            "Biography",
            {
                "classes": ("collapse",),
                "fields": ("summary", "image", "biography"),
            },
        ),
        (
            "Honorifics",
            {
                "classes": ("collapse",),
                "fields": ("honorific_prefix", "honorific_suffix"),
            },
        ),
        (
            "Demography",
            {"classes": ("collapse",), "fields": ("national_identity",)},
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
            "Advanced options",
            {"classes": ("collapse",), "fields": ("start_date", "end_date")},
        ),
    )
    # inlines = generics.BASE_INLINES + [MembershipInline]


class PersonExtraFieldValueAdminForm(ModelForm):
    pass


class ExtraFieldAdminForm(ModelForm):
    pass


@admin.register(ComplexPopoloField)
class ComplexPopoloFieldAdmin(admin.ModelAdmin):
    list_display = ["name", "label", "order"]
    ordering = ("order",)


@admin.register(PersonExtraFieldValue)
class PersonExtraFieldValueAdmin(admin.ModelAdmin):
    form = PersonExtraFieldValueAdminForm


@admin.register(ExtraField)
class ExtraFieldAdmin(admin.ModelAdmin):
    form = ExtraFieldAdminForm


admin.site.register(Person, PersonAdmin)
