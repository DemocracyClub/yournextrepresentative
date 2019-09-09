from django.contrib import admin
from django.forms import ModelForm

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
            "Advanced options",
            {"classes": ("collapse",), "fields": ("start_date", "end_date")},
        ),
    )
    # inlines = generics.BASE_INLINES + [MembershipInline]


admin.site.register(Person, PersonAdmin)
