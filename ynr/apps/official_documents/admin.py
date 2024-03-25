from django.contrib import admin

from .models import BallotSOPN, ElectionSOPN


class ElectionSOPNAdmin(admin.ModelAdmin):
    list_display = ("created", "election", "source_url")
    search_fields = ("ballot__ballot_paper_id", "source_url")
    ordering = ("-created",)


class BallotSOPNAdmin(admin.ModelAdmin):
    list_display = ("created", "ballot", "source_url")
    search_fields = ("ballot__ballot_paper_id", "source_url")
    ordering = ("-created",)


admin.site.register(BallotSOPN, BallotSOPNAdmin)
admin.site.register(ElectionSOPN, ElectionSOPNAdmin)
