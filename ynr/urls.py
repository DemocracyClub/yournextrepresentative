from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path, re_path
from django.views.generic import TemplateView


def trigger_error(request):
    return 1 / 0


urlpatterns = [
    re_path(r"^parties/", include("parties.urls")),
    re_path(r"^", include("api.urls")),
    re_path(r"^", include("elections.urls")),
    re_path(r"", include("facebook_data.urls")),
    re_path(r"^", include("candidates.urls")),
    re_path(r"^", include("people.urls")),
    re_path(r"^", include("search.urls")),
    re_path(r"^admin/doc/", include("django.contrib.admindocs.urls")),
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^upload_document/", include("official_documents.urls")),
    re_path(r"^results/", include("results.urls")),
    re_path(r"^duplicates/", include("duplicates.urls")),
    re_path(r"^wombles/", include("wombles.urls")),
    re_path(r"^data/", include("data_exports.urls")),
    path(
        "volunteer/",
        TemplateView.as_view(template_name="volunteer.html"),
        name="volunteer-view",
    ),
    re_path(r"", include("ynr_refactoring.urls")),
    re_path(
        r"^robots\.txt$",
        TemplateView.as_view(
            template_name="robots.txt", content_type="text/plain"
        ),
    ),
    path("sentry-debug/", trigger_error),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [re_path(r"^__debug__/", include(debug_toolbar.urls))]

if settings.DEBUG or getattr(settings, "RUNNING_TESTS", False):
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
