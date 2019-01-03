import sys

from django.conf import settings
from django.conf.urls import include, url
from django.views.generic import TemplateView

from django.contrib import admin

from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    url(r"^parties/", include("parties.urls")),
    url(r"^", include("api.urls")),
    url(r"^", include("elections.urls")),
    url(r"^", include("candidates.urls")),
    url(r"^admin/doc/", include("django.contrib.admindocs.urls")),
    url(r"^admin/", admin.site.urls),
    url(r"^accounts/", include("allauth.urls")),
    url(r"^upload_document/", include("official_documents.urls")),
    url(r"^results/", include("results.urls")),
    url(r"", include("ynr_refactoring.urls")),
    url(
        r"^robots\.txt$",
        TemplateView.as_view(
            template_name="robots.txt", content_type="text/plain"
        ),
    ),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [url(r"^__debug__/", include(debug_toolbar.urls))]

if settings.DEBUG or getattr(settings, "RUNNING_TESTS", False):
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "ynr_refactoring.views.logged_page_not_found_wrapper"
