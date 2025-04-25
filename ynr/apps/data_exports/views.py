import datetime
from typing import List, Union

from cached_counts.models import ElectionReport
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.utils.text import slugify
from django.views import View
from django.views.generic import TemplateView

from .csv_fields import csv_fields, get_core_fieldnames
from .filters import (
    create_materialized_membership_filter,
)
from .forms import AdditionalFieldsForm, grouped_choices
from .models import MaterializedMemberships, MaterializedMembershipsQuerySet


class DataFilterMixin:
    def get_queryset(self):
        return MaterializedMemberships.objects.all()

    def get_filter_data(self, **kwargs):
        context = {}
        context["extra_fields"] = []
        additional_fields_form = AdditionalFieldsForm(data=self.request.GET)
        if additional_fields_form.is_valid():
            context["extra_fields"] = additional_fields_form.cleaned_data[
                "extra_fields"
            ]

        context["csv_fields"] = grouped_choices()

        context["additional_fields_form"] = additional_fields_form

        for field_name, field in csv_fields.items():
            if field.core:
                continue
            if field.value_group in self.request.GET.getlist("field_group"):
                context["extra_fields"].append(field_name)

        context["headers"] = get_core_fieldnames() + context["extra_fields"]

        qs = self.get_queryset()
        qs = qs.for_data_table(extra_fields=context["extra_fields"])
        filter_set = create_materialized_membership_filter(
            [
                (field_name, csv_fields[field_name])
                for field_name in context["extra_fields"]
            ]
        )(
            self.request.GET,
            queryset=qs,
        )

        queryset = filter_set.qs
        context["objects"]: Union[
            MaterializedMembershipsQuerySet, List[MaterializedMemberships]
        ] = queryset
        context["filter_set"] = filter_set

        return context


class DataCustomBuilderView(DataFilterMixin, TemplateView):
    """
    A view for presenting all options for getting all data out of this site
    """

    template_name = "data_exports/custom_builder.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(self.get_filter_data())

        paginator = Paginator(
            context["objects"],
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


class DataShortcutView(TemplateView):
    template_name = "data_exports/data_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get loads of recent elections for this page
        context[
            "charismatic_elections"
        ] = ElectionReport.objects.all().order_by("-election_date")
        context["special_reports"] = [
            {
                "only_by_elections": True,
                "election_type": "local",
                "title": "Local by-elections",
            },
            {
                "only_by_elections": True,
                "election_type": "parl",
                "title": "Parliamentary by-elections",
            },
        ]

        return context
