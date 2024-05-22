import datetime
from typing import List, Union

from django.core.paginator import Paginator
from django.http import HttpResponse
from django.utils.text import slugify
from django.views import View
from django.views.generic import TemplateView

from .csv_fields import csv_fields, get_core_fieldnames
from .filters import MaterializedMembershipFilter
from .forms import AdditionalFieldsForm, grouped_choices
from .models import MaterializedMemberships, MaterializedMembershipsQuerySet


class DataFilterMixin:
    def get_queryset(self):
        return MaterializedMemberships.objects.all()

    def get_filter_data(self, **kwargs):
        context = {}
        qs = self.get_queryset()
        filter_set = MaterializedMembershipFilter(self.request.GET, queryset=qs)

        additional_fields_form = AdditionalFieldsForm(data=self.request.GET)
        context["csv_fields"] = grouped_choices()
        context["extra_fields"] = []
        if additional_fields_form.is_valid():
            context["extra_fields"] = additional_fields_form.cleaned_data[
                "extra_fields"
            ]

        context["additional_fields_form"] = additional_fields_form

        for field_name, field in csv_fields.items():
            if field.core:
                continue
            if field.value_group in self.request.GET.getlist("field_group"):
                context["extra_fields"].append(field_name)

        context["headers"] = get_core_fieldnames() + context["extra_fields"]

        queryset = filter_set.qs
        context["objects"]: Union[
            MaterializedMembershipsQuerySet, List[MaterializedMemberships]
        ] = queryset
        context["filter_set"] = filter_set

        return context


class DataHomeView(DataFilterMixin, TemplateView):
    """
    A view for presenting all options for getting all data out of this site
    """

    template_name = "data_exports/data_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(self.get_filter_data())

        paginator = Paginator(
            context["objects"].for_data_table(
                extra_fields=context["extra_fields"]
            ),
            50,
        )
        page = paginator.get_page(self.request.GET.get("page", "1"))
        context["page_obj"] = page
        return context


class DataExportView(DataFilterMixin, View):
    def get(self, request, *args, **kwargs):
        context = self.get_filter_data()
        content_type = "text/csv"
        date_str = datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        filename_dict = dict(context["filter_set"].data)
        filename_dict.pop("format", None)
        file_str = slugify(
            "__".join(f"{key}_{value}" for key, value in filename_dict.items())
        )
        headers = {
            "Content-Disposition": f'attachment; filename="dc-candidates-{file_str}-{date_str}.csv"'
        }

        response = HttpResponse(
            content_type=content_type,
            headers=headers,
        )
        context["objects"].write_csv(
            response, extra_fields=context["extra_fields"]
        )
        return response
