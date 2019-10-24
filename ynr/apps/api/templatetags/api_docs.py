import sys
from django.utils.safestring import mark_safe

from django import template
from django.urls import reverse
from drf_yasg.openapi import SchemaRef

register = template.Library()


@register.filter
def link_to_definition(value, version="next"):
    ref_id = None
    if type(value) in (SchemaRef, dict):
        ref_id = value["$ref"]
    if type(value) == tuple:
        ref_id = value[1]

    if ref_id:
        class_name = ref_id.split("/")[-1]
        url = reverse("api_docs_{}_definitions".format(version))
        return mark_safe(
            """<a href="{url}#{class_name}">{class_name}</a>""".format(
                ref_id=ref_id, class_name=class_name, url=url
            )
        )
    else:
        return value


@register.filter
def format_docstring(docstring):
    docstring = str(docstring)
    if not docstring:
        return ""
        # Convert tabs to spaces (following the normal Python rules)
        # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxsize
    while not lines[0]:
        lines.pop(0)
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return "\n".join(trimmed)
