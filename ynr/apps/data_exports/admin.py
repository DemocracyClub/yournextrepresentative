from django.contrib import admin

from .models import CSVDownloadLog, CSVDownloadReason


@admin.register(CSVDownloadReason)
class CSVDownloadReasonAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "email",
        "usage_reason",
        "created",
    )
    search_fields = ("user__username", "email", "usage_reason")

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(CSVDownloadLog)
class CSVDownloadLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "query_params",
        "created",
    )
    search_fields = ("user__username",)

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
