from data_exports import views
from django.urls import path

urlpatterns = [
    path(r"shortcuts", views.DataShortcutView.as_view(), name="data_shortcuts"),
    path(
        r"", views.DataCustomBuilderView.as_view(), name="data_custom_builder"
    ),
    path(r"export_csv/", views.DataExportView.as_view(), name="data_export"),
    path(
        r"download_reason/",
        views.CSVDownloadReasonView.as_view(),
        name="download_reason",
    ),
    path(
        r"download_thanks/",
        views.CSVDownloadThanksView.as_view(),
        name="download_thanks",
    ),
]
