from collections import OrderedDict

from django.views.generic import TemplateView

from rest_framework.request import Request
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator


class OpenAPISchemaMixin:
    version = None
    patterns = None

    def _sort_ordered_dict_by_keys(self, od):
        keys = sorted(list(od.keys()))
        new_od = OrderedDict()
        for key in keys:
            if type(od[key]) == OrderedDict:
                od[key] = self._sort_ordered_dict_by_keys(od[key])
            new_od[key] = od[key]
        return new_od

    def get_schema(self):
        schema = OpenAPISchemaGenerator(
            openapi.Info(
                title="Snippets API",
                default_version="self.version",
                description="Test description",
                terms_of_service="https://www.google.com/policies/terms/",
                contact=openapi.Contact(email="hello@democracyclub.org.uk"),
                license=openapi.License(name="BSD License"),
            ),
            patterns=self.patterns,
            version="next",
        )
        request = Request(self.request)
        schema_obj = schema.get_schema(request=request, public=True)

        return self._sort_ordered_dict_by_keys(schema_obj)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["schema"] = self.get_schema()
        context["version"] = self.version
        return context


class NextAPIDocsView(OpenAPISchemaMixin, TemplateView):
    template_name = "api/next_home.html"


class APIDocsEndpointsView(OpenAPISchemaMixin, TemplateView):
    template_name = "api/endpoints.html"


class APIDocsDefinitionsView(OpenAPISchemaMixin, TemplateView):
    template_name = "api/definitions.html"
    patterns = None
    version = "next"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["schema"] = self.get_schema()
        return context
