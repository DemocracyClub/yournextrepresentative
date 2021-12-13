import re

from dateutil import parser
from django.conf import settings
from django_date_extensions.fields import ApproximateDate

from candidates.twitter_api import TwitterAPITokenMissing, get_twitter_user_id


def parse_approximate_date(s):
    """Take any reasonable date string, and return an ApproximateDate for it

    >>> ad = parse_approximate_date('2014-02-17')
    >>> type(ad)
    <class 'django_date_extensions.fields.ApproximateDate'>
    >>> ad
    2014-02-17
    >>> parse_approximate_date('2014-02')
    2014-02-00
    >>> parse_approximate_date('2014')
    2014-00-00
    >>> parse_approximate_date('future')
    future
    """

    for regexp in [
        r"^(\d{4})-(\d{2})-(\d{2})$",
        r"^(\d{4})-(\d{2})$",
        r"^(\d{4})$",
    ]:
        m = re.search(regexp, s)
        if m:
            return ApproximateDate(*(int(g, 10) for g in m.groups()))
    if s == "future":
        return ApproximateDate(future=True)
    if s:
        dt = parser.parse(
            s,
            parserinfo=localparserinfo(),
            dayfirst=settings.DD_MM_DATE_FORMAT_PREFERRED,
        )
        return ApproximateDate(dt.year, dt.month, dt.day)
    raise ValueError("Couldn't parse '{}' as an ApproximateDate".format(s))


class localparserinfo(parser.parserinfo):
    MONTHS = [
        ("Jan", "Jan", "January", "January"),
        ("Feb", "Feb", "February", "February"),
        ("Mar", "Mar", "March", "March"),
        ("Apr", "Apr", "April", "April"),
        ("May", "May", "May", "May"),
        ("Jun", "Jun", "June", "June"),
        ("Jul", "Jul", "July", "July"),
        ("Aug", "Aug", "August", "August"),
        ("Sep", "Sep", "Sept", "September", "September"),
        ("Oct", "Oct", "October", "October"),
        ("Nov", "Nov", "November", "November"),
        ("Dec", "Dec", "December", "December"),
    ]

    PERTAIN = ["of", "of"]


def squash_whitespace(s):
    # Take any run of more than one whitespace character, and replace
    # it either with a newline (if that replaced text contained a
    # newline) or a space (otherwise).
    return re.sub(
        r"(?ims)\s+", lambda m: "\n" if "\n" in m.group(0) else " ", s
    )


def clean_twitter_username(username):
    # Remove any URL bits around it:
    username = username.strip()
    m = re.search(r"^.*twitter.com/(\w+)", username)
    if m:
        username = m.group(1)
    # If there's a leading '@', strip that off:
    username = re.sub(r"^@", "", username)
    if not re.search(r"^\w*$", username):
        message = "The Twitter username must only consist of alphanumeric characters or underscore"
        raise ValueError(message)
    if username:
        try:
            user_id = get_twitter_user_id(username)
            if not user_id:
                message = "The Twitter account {screen_name} doesn't exist"
                raise ValueError(message.format(screen_name=username))
        except TwitterAPITokenMissing:
            # If there's no API token, we can't check the screen name,
            # but don't fail validation because the site owners
            # haven't set that up.
            return username
    return username


def clean_wikidata_id(identifier):
    identifier = identifier.strip().lower()
    m = re.search(r"^.*wikidata.org/(wiki|entity)/(\w+)", identifier)
    if m:
        identifier = m.group(2)
    identifier = identifier.upper()
    if not re.match(r"Q[\d]+", identifier):
        raise ValueError("Wikidata ID be a 'Q12345' type identifier")
    return identifier
