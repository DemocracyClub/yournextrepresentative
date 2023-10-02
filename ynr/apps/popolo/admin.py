from django import forms
from django.contrib import admin
from django.forms import ValidationError
from popolo import models

from .behaviors import admin as generics


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


class MembershipAdminForm(forms.ModelForm):
    class Meta:
        model = models.Membership
        fields = "__all__"

    def clean(self):
        if (
            self.cleaned_data["deselected"]
            and not self.cleaned_data["deselected_source"]
        ):
            raise ValidationError(
                "A deselected membership must have a deselected source. Please add one. "
            )
        if (
            not self.cleaned_data["deselected"]
            and self.cleaned_data["deselected_source"]
        ):
            raise ValidationError(
                "A membership with a deselected source must be deselected. "
            )
        return super().clean()


class MembershipAdmin(admin.ModelAdmin):
    form = MembershipAdminForm
    model = models.Membership
    list_display = ("person", "party", "get_ballot", "deselected")
    fields = ("person", "party", "ballot", "deselected", "deselected_source")
    readonly_fields = ("person", "party", "ballot")
    list_filter = ("deselected",)

    @admin.display(description="Ballot")
    def get_ballot(self, obj):
        return obj.ballot.ballot_paper_id


admin.site.register(models.Membership, MembershipAdmin)
admin.site.register(models.Post, PostAdmin)
admin.site.register(models.Organization, OrganizationAdmin)
