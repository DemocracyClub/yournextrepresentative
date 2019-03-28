from django.contrib import admin

from .models import SiteBanner


class SiteBannerAdmin(admin.ModelAdmin):
    pass


admin.site.register(SiteBanner, SiteBannerAdmin)
