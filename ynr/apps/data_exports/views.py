import datetime
from typing import Dict, List, Union
from urllib.parse import urlencode

from cached_counts.models import ElectionReport
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.utils.text import slugify
from django.views import View
from django.views.generic import CreateView, TemplateView

from .csv_fields import csv_fields, get_core_fieldnames
from .filters import (
    create_materialized_membership_filter,
)
from .forms import AdditionalFieldsForm, CSVDownloadReasonForm, grouped_choices
from .models import (
    CSVDownloadReason,
    MaterializedMemberships,
    MaterializedMembershipsQuerySet,
)


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
        if "download" not in self.request.GET and (
            request.user.is_authenticated
            and not CSVDownloadReason.objects.filter(user=request.user).exists()
        ):
            url = reverse("download_reason")
            url = f"{url}?{self.request.GET.urlencode()}"
            return HttpResponseRedirect(url)

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
            {
                "only_by_elections": None,
                "election_type": "",
                "title": "All candidates",
            },
        ]

        return context


def reverse_with_query_params(view_name, query_params, extra: Dict = None):
    url = f"{reverse(view_name)}?{query_params.urlencode()}"
    if not extra:
        return url

    return f"{url}&{urlencode(extra)}"


class CSVDownloadReasonView(CreateView):
    model = CSVDownloadReason
    form_class = CSVDownloadReasonForm
    template_name = "data_exports/download_reason.html"

    def get_form_kwargs(self):
        """
        Pass `user` into the form so __init__ can pop or require email.
        """
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse_with_query_params("download_thanks", self.request.GET)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["download_url"] = reverse_with_query_params(
            "data_export", self.request.GET, {"download": 1}
        )
        return context

    def form_valid(self, form):
        """
        Attach the user (if authenticated) and clear email if it's been popped.
        """
        self.object = form.save(commit=False)
        if self.request.user.is_authenticated:
            self.object.user = self.request.user
            # ensure we don't keep an email on authenticated submissions
            self.object.email = ""
        # otherwise, .email was filled in by the form
        self.object.save()
        return super().form_valid(form)


class CSVDownloadThanksView(TemplateView):
    template_name = "data_exports/download_thanks.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["download_url"] = reverse_with_query_params(
            "data_export", self.request.GET, {"download": 1}
        )
        return context
