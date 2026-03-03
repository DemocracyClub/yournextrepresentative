from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User


class CustomUserAdmin(UserAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["is_superuser"].help_text = (
            "Assigns this user all the user permissions. "
            "This allows the user to do everything in the admin. "
            "To give users permissions in the frontend, use the groups."
        )
        return form


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
