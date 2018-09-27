from django.conf import settings
from django.contrib import admin

from .models import Election

CAN_EDIT_ELECTIONS = getattr(settings, "CAN_EDIT_ELECTIONS", True)


class ElectionAdmin(admin.ModelAdmin):
    list_display = ("name", "election_date", "description", "current")
    search_fields = ("name", "slug")
    ordering = ("-election_date", "name")

    def has_add_permission(self, request, obj=None):
        return CAN_EDIT_ELECTIONS

    def has_delete_permission(self, request, obj=None):
        return CAN_EDIT_ELECTIONS

    def get_readonly_fields(self, request, obj=None):
        if CAN_EDIT_ELECTIONS:
            return list(self.readonly_fields)
        else:
            return (
                list(self.readonly_fields)
                + [field.name for field in obj._meta.fields]
                + [field.name for field in obj._meta.many_to_many]
            )


admin.site.register(Election, ElectionAdmin)
