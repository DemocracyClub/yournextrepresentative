from django.contrib import admin

from popolo import models

from .behaviors import admin as generics

try:
    pass
except ImportError:
    pass


class PostAdmin(admin.ModelAdmin):
    model = models.Post
    fieldsets = (
        (None, {"fields": ("label", "role", "start_date", "end_date")}),
        (
            "Details",
            {
                "classes": ("collapse",),
                "fields": ("other_label", "organization"),
            },
        ),
    )
    inlines = [generics.ContactDetailAdmin, generics.SourceAdmin]


class OrganizationAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("name", "founding_date", "dissolution_date")}),
        (
            "Details",
            {
                "classes": ("collapse",),
                "fields": ("summary", "image", "description"),
            },
        ),
        (
            "Advanced options",
            {
                "classes": ("collapse",),
                "fields": ("classification", "start_date", "end_date"),
            },
        ),
    )
    inlines = generics.BASE_INLINES


admin.site.register(models.Post, PostAdmin)
admin.site.register(models.Organization, OrganizationAdmin)
