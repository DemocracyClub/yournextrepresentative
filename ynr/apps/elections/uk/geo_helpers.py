# coding=utf-8

from __future__ import unicode_literals

import re
import logging

import requests

from django.conf import settings
from django.core.cache import cache
from django.utils.http import urlquote
from django.utils.six.moves.urllib_parse import urljoin
from django.utils.translation import ugettext as _

from candidates.models import PostExtraElection


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
    settings, "EE_BASE_URL", "https://elections.democracyclub.org.uk/")


def get_post_elections(url, cache_key, exception):
    r = requests.get(url)
    if r.status_code == 200:
        ee_result = r.json()
        ballot_paper_ids = [
            e['election_id']
            for e in ee_result['results']
            if not e['group_type']]
        pee_qs = PostExtraElection.objects.filter(
            ballot_paper_id__in=ballot_paper_ids,
            election__current=True)
        cache.set(cache_key, pee_qs, settings.EE_CACHE_SECONDS)
        return pee_qs
    elif r.status_code == 400:
        ee_result = r.json()
        raise exception(ee_result['detail'])
    elif r.status_code == 404:
        raise exception(
            _('The url "{}" couldn’t be found').format(url)
        )
    else:
        raise UnknownGeoException(
            _('Unknown error for "{0}"').format(
                url
            )
        )


def get_post_elections_from_postcode(original_postcode):
    postcode = re.sub(r'(?ms)\s*', '', original_postcode.lower())
    if re.search(r'[^a-z0-9]', postcode):
        raise BadPostcodeException(
            _('There were disallowed characters in "{0}"').format(
                original_postcode)
        )
    cache_key = 'geolookup-postcodes:' + postcode
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    url = urljoin(EE_BASE_URL, "/api/elections/?postcode={}".format(
        urlquote(postcode)))
    try:
        areas = get_post_elections(url, cache_key, BadPostcodeException)
    except BadPostcodeException:
        # Give a nicer error message, as this is used on the frontend
        raise BadPostcodeException(
            'The postcode “{}” couldn’t be found'.format(original_postcode))
    return areas


def get_post_elections_from_coords(coords):
    url = urljoin(EE_BASE_URL, "/api/elections/?coords={}".format(
        urlquote(coords)))

    cache_key = 'geolookup-coords:' + coords
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    return get_post_elections(url, cache_key, BadCoordinatesException)
