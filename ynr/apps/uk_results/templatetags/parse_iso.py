from dateutil import parser
from django.template import Library

register = Library()


@register.filter(expects_localtime=True)
def parse_iso(value):
    return parser.parse(value)
