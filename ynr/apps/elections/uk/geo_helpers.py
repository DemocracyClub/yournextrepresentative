# coding=utf-8


import re
import logging

import requests

from django.conf import settings
from django.core.cache import cache
from django.utils.http import urlquote
from django.utils.six.moves.urllib_parse import urljoin

from candidates.models import Ballot


class BaseMapItException(Exception):
    pass


class BadPostcodeException(BaseMapItException):
    pass


class BadCoordinatesException(BaseMapItException):
    pass


class UnknownGeoException(BaseMapItException):
    pass


logger = logging.getLogger(__name__)

EE_BASE_URL = getattr(
    settings, "EE_BASE_URL", "https://elections.democracyclub.org.uk/"
)


def get_ballots(url, cache_key, exception):
    r = requests.get(url)
    if r.status_code == 200:
        ee_result = r.json()
        ballot_paper_ids = [
            e["election_id"]
            for e in ee_result["results"]
            if not e["group_type"]
        ]
        ballot_qs = Ballot.objects.current_or_future().filter(
            ballot_paper_id__in=ballot_paper_ids
        )
        cache.set(cache_key, ballot_qs, settings.EE_CACHE_SECONDS)
        return ballot_qs
    elif r.status_code == 400:
        ee_result = r.json()
        raise exception(ee_result["detail"])
    elif r.status_code == 404:
        raise exception('The url "{}" couldn’t be found'.format(url))
    else:
        raise UnknownGeoException('Unknown error for "{0}"'.format(url))


def get_ballots_from_postcode(original_postcode):
    postcode = re.sub(r"(?ms)\s*", "", original_postcode.lower())
    if re.search(r"[^a-z0-9]", postcode):
        raise BadPostcodeException(
            'There were disallowed characters in "{0}"'.format(
                original_postcode
            )
        )
    cache_key = "geolookup-postcodes:" + postcode
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    url = urljoin(
        EE_BASE_URL, "/api/elections/?postcode={}".format(urlquote(postcode))
    )
    try:
        areas = get_ballots(url, cache_key, BadPostcodeException)
    except BadPostcodeException:
        # Give a nicer error message, as this is used on the frontend
        raise BadPostcodeException(
            "The postcode “{}” couldn’t be found".format(original_postcode)
        )
    return areas


def get_ballots_from_coords(coords):
    url = urljoin(
        EE_BASE_URL, "/api/elections/?coords={}".format(urlquote(coords))
    )

    cache_key = "geolookup-coords:" + coords
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    return get_ballots(url, cache_key, BadCoordinatesException)
