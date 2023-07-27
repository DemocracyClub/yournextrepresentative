from datetime import date

from django import template
from django.template.defaultfilters import date as date_tag

register = template.Library()


@register.filter
def format_approximate_date(approximate_date):
    """
    Turn an approximate date in to a formatted string, even if some date parts
    aren't there
    """
    fmt = ["Y"]

    if approximate_date.month:
        fmt.append("F")
    else:
        approximate_date.month = 1

    if approximate_date.day:
        fmt.append("jS")
    else:
        approximate_date.day = 1

    fmt_str = " ".join(reversed(fmt))
    return date_tag(
        date(
            approximate_date.year, approximate_date.month, approximate_date.day
        ),
        fmt_str,
    )
