from data_exports import views
from django.urls import path

urlpatterns = [
    path(r"", views.DataHomeView.as_view(), name="data_home"),
    path(r"export_csv/", views.DataExportView.as_view(), name="data_export"),
]
