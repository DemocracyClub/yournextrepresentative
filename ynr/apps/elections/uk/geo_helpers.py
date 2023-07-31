# coding=utf-8


import logging
import re
from urllib.parse import quote, urljoin

import requests
from candidates.models import Ballot
from django.conf import settings
from django.core.cache import cache


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


def ballot_paper_ids_from_ee(url, cache_key, exception):
    r = requests.get(url)
    if r.status_code == 200:
        ee_result = r.json()
        ballot_paper_ids = [
            e["election_id"]
            for e in ee_result["results"]
            if not e["group_type"]
        ]
        cache.set(cache_key, ballot_paper_ids, settings.EE_CACHE_SECONDS)
        return ballot_paper_ids
    if r.status_code == 400:
        ee_result = r.json()
        raise exception(ee_result["detail"])
    if r.status_code == 404:
        raise exception(f'The url "{url}" couldn’t be found')
    raise UnknownGeoException(f'Unknown error for "{url}"')


def get_ballots(url, cache_key, exception):
    return Ballot.objects.filter(
        ballot_paper_id__in=ballot_paper_ids_from_ee(url, cache_key, exception)
    )


def get_ballots_from_postcode(
    original_postcode, current_only=True, ids_only=False
):
    postcode = re.sub(r"(?ms)\s*", "", original_postcode.lower())
    if re.search(r"[^a-z0-9]", postcode):
        raise BadPostcodeException(
            f'There were disallowed characters in "{original_postcode}"'
        )
    cache_key = f"geolookup-postcodes:{current_only}:{postcode}"
    cached_result = cache.get(cache_key)
    if cached_result:
        if ids_only:
            # return list of IDS from cache
            return cached_result
        return Ballot.objects.filter(ballot_paper_id__in=cached_result)

    url = urljoin(EE_BASE_URL, f"/api/elections/?postcode={quote(postcode)}")
    if current_only:
        url = f"{url}&current=1"
    try:
        if ids_only:
            return ballot_paper_ids_from_ee(
                url, cache_key, BadPostcodeException
            )
        return get_ballots(url, cache_key, BadPostcodeException)
    except BadPostcodeException:
        # Give a nicer error message, as this is used on the frontend
        raise BadPostcodeException(
            f"The postcode “{original_postcode}” couldn’t be found"
        )


def get_ballots_from_coords(coords, current_only=True):
    url = urljoin(EE_BASE_URL, f"/api/elections/?coords={quote(coords)}")
    if current_only:
        url = f"{url}&current=1"
    cache_key = f"geolookup-coords:{current_only}:{coords}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return Ballot.objects.filter(ballot_paper_id__in=cached_result)

    return get_ballots(url, cache_key, BadCoordinatesException)
