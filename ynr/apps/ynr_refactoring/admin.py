from django.contrib import admin

from .models import PageNotFoundLog


@admin.register(PageNotFoundLog)
class PageNotFoundLogAdmin(admin.ModelAdmin):
    list_filter = ("root_path", "created")
    list_display = ["url", "created"]
    ordering = ("-created",)
