from django.template import Library
from dateutil import parser

register = Library()

@register.filter(expects_localtime=True)
def parse_iso(value):
    return parser.parse(value)
