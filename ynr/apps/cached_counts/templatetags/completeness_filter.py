from urllib.parse import urlencode

from django import template

register = template.Library()


@register.inclusion_tag("completeness_filter_links.html", takes_context=True)
def completeness_filter_links(context, field_name):
    request = context["request"]
    current_params = request.GET.copy()
    base_url = request.path

    has_key = f"has_{field_name}"
    has_value = current_params.get(has_key)

    def link_with_param(value):
        params = current_params.copy()
        params[has_key] = value
        return f"{base_url}?{urlencode(params)}"

    def link_without_param():
        params = current_params.copy()
        params.pop(has_key, None)
        return f"{base_url}?{urlencode(params)}"

    return {
        "with_url": link_with_param("yes"),
        "without_url": link_with_param("no"),
        "all_url": link_without_param(),
        "has_value": has_value,
    }


@register.simple_tag
def model_attr(model, attr):
    return getattr(model, attr) or ""
