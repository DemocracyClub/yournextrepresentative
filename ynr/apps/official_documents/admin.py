from django.contrib import admin

from .models import OfficialDocument


class OfficialDocumentAdmin(admin.ModelAdmin):
    list_display = ("document_type", "created", "post_election", "source_url")
    search_fields = ("post_election", "source_url")
    list_filter = ("document_type",)
    ordering = ("-created",)


admin.site.register(OfficialDocument, OfficialDocumentAdmin)
