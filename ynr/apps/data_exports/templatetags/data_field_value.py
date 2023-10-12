from data_exports.csv_fields import csv_fields
from django import template

register = template.Library()


@register.simple_tag
def data_cell(heading_name, obj):
    value = obj[heading_name]
    if csv_fields[heading_name].formatter:
        value = csv_fields[heading_name].formatter(value)
    if value is None:
        return ""
    return value
