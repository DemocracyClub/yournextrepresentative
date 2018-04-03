import datetime
from dateutil import parser

from django.conf import settings


def site_wide_messages(request):
    """
    Looks in settings for a var called SITE_WIDE_MESSAGES that is a list
    of dicts that looks like this:

    {
        'message': "lorem",
        'show_until': "2018-04-10T18:00",
        'url': "https://democracyclub.org.uk"
    }
    """
    messages = []
    for message in getattr(settings, 'SITE_WIDE_MESSAGES', []):
        if message.get('show_until'):
            if parser.parse(message['show_until']) > datetime.datetime.now():
                messages.append(message)
    return {'site_wide_messages': messages}
