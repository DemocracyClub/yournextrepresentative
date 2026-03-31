from django.contrib import admin, messages

from .models import Party, PartyDescription


@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    search_fields = ("name", "ec_id")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in obj._meta.concrete_fields] if obj else []


@admin.register(PartyDescription)
class PartyDescriptionAdmin(admin.ModelAdmin):
    list_display = (
        "description",
        "party",
        "active",
        "pseudo_description",
        "date_description_approved",
    )
    list_filter = ("active", "pseudo_description")
    search_fields = ("description", "party__name")
    autocomplete_fields = ("party",)
    ordering = ("party__name", "description")

    def has_delete_permission(self, request, obj=None):
        return False

    def get_changeform_initial_data(self, request):
        return {"pseudo_description": True}

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is None:
            form.base_fields["pseudo_description"].help_text = """
            Pseudo-description means a description we've manually added,
            as opposed to one that is imported from the Electoral Commission register.
            If you are creating a new description in the admin, this should be checked.
            """
        return form

    def get_readonly_fields(self, request, obj=None):
        if obj is not None and not obj.pseudo_description:
            return [f.name for f in obj._meta.concrete_fields]
        return super().get_readonly_fields(request, obj)

    def changeform_view(
        self, request, object_id=None, form_url="", extra_context=None
    ):
        if object_id:
            obj = self.get_object(request, object_id)
            if obj is not None and not obj.pseudo_description:
                self.message_user(
                    request,
                    "This party description was imported from the Electoral Commission register. You can't edit it here.",
                    level=messages.WARNING,
                )
        return super().changeform_view(
            request, object_id, form_url, extra_context
        )
