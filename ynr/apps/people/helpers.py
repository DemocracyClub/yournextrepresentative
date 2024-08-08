import contextlib
import re
from urllib.parse import urlparse, urlunparse

from candidates.mastodon_api import (
    MastodonAPITokenMissing,
    verify_mastodon_account,
)
from dateutil import parser
from django.conf import settings
from django_date_extensions.fields import ApproximateDate


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


def clean_mastodon_username(username):
    # Accounts can be on any domain name and we can expect we can get valid
    # input in at least two formats: @username@domain.com or domain.com/@username.
    # Both are valid formats, and to verify the acount is valid, we will need
    # to extract the domain.
    parsed_username = urlparse(username)

    if (
        not parsed_username.scheme
        or not parsed_username.netloc
        or not parsed_username.path
    ) or not re.search(r"^/@", parsed_username.path):
        message = "The Mastodon account must follow the format https://domain/@username. The domain can be any valid Mastodon domain name."
        raise ValueError(message)
    name = parsed_username.path
    name = re.sub(r"^/@", "", name)
    name = re.sub(r"/$", "", name)
    name = name.strip()
    domain = parsed_username.netloc
    domain = domain.strip()

    username = "https://{domain}/@{name}".format(domain=domain, name=name)
    # if the format is correct, check that the account exists
    if username:
        with contextlib.suppress(MastodonAPITokenMissing):
            # If there's no API token, we can't check the screen name,
            # but don't fail validation
            verify_mastodon_account(domain, name)
    return username


def clean_twitter_username(username):
    # Remove any URL bits around it:
    username = username.strip()
    m = re.search(r"^.*(twitter.com|x.com)/(\@?)(\w+)", username)
    if m:
        username = m.group(3)
    # If there's a leading '@', strip that off:
    username = re.sub(r"^@", "", username)
    if not re.search(r"^\w*$", username):
        message = "The Twitter username must only consist of alphanumeric characters or underscore"
        raise ValueError(message)
    return username


def clean_linkedin_url(url):
    parsed_url = urlparse(url)
    valid = True
    if not re.match(r"([^.]+)?\.linkedin.com$", parsed_url.netloc):
        valid = False
    path = parsed_url.path
    if path.startswith("/pub/"):
        parts = path.split("/")
        name = parts[2]
        id_parts = parts[3:]
        user_id = "".join(id_parts[::-1])
        path = f"/in/{name}-{user_id}/"

    if not path.startswith("/in/"):
        valid = False

    if not valid:
        raise ValueError("Please enter a valid LinkedIn URL.")
    return urlunparse(parsed_url._replace(path=path))


def clean_instagram_url(url):
    parsed_username = urlparse(url)
    if not parsed_username.scheme:
        url = f"https://{url}"
        parsed_username = urlparse(url)

    if parsed_username.netloc and parsed_username.netloc not in [
        "instagram.com",
        "www.instagram.com",
        "instagr.am",
        "www.instagr.am",
    ]:
        raise ValueError(
            "The Instagram URL must be from a valid Instagram domain."
        )
    username = parsed_username.path.strip("/")
    # RegEx thanks to https://blog.jstassen.com/2016/03/code-regex-for-instagram-username-and-hashtags/
    if not re.match(
        r"(?:@?)([A-Za-z0-9_](?:(?:[A-Za-z0-9_]|(?:\.(?!\.))){0,28}(?:[A-Za-z0-9_]))?)$",
        username,
    ):
        raise ValueError("This is not a valid Instagram URL. Please try again.")
    return f"https://www.instagram.com/{username}/"


def clean_wikidata_id(identifier):
    identifier = identifier.strip().lower()
    m = re.search(r"^.*wikidata.org/(wiki|entity)/(\w+)", identifier)
    if m:
        identifier = m.group(2)
    identifier = identifier.upper()
    if not re.match(r"Q[\d]+", identifier):
        raise ValueError("Wikidata ID be a 'Q12345' type identifier")
    return identifier


def person_names_equal(name, other_name):
    def _normalize(name):
        name = name.lower()
        return name.replace(" ", "")

    return _normalize(name) == _normalize(other_name)
