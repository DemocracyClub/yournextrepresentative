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

from candidates.mapit import (
    BaseMapItException, BadPostcodeException,
    UnknownMapitException, BadCoordinatesException
)


logger = logging.getLogger(__name__)

EE_URL_BASE = "https://elections.democracyclub.org.uk"


class NoConstituencyForPostcodeException(BaseMapItException):
    pass


class MapItAreaNotFoundException(BaseMapItException):
    pass


def get_known_area_types(ee_areas):
    result = []
    for election in ee_areas['results']:
        if election['group_type'] == 'election':
            continue
        if election['group_type'] == 'organisation':
            area_type = election['organisation']['organisation_type']
            area_id = ":".join(
                [area_type, election['organisation']['official_identifier']])
        else:
            area_id = election['division']['official_identifier']
            area_type = election['division']['division_type']

        result.append((
            area_type,
            area_id
        ))

    return result


def get_areas(url, cache_key, exception):
    r = requests.get(url)
    if r.status_code == 200:
        ee_result = r.json()
        result = get_known_area_types(ee_result)
        cache.set(cache_key, result, settings.MAPIT_CACHE_SECONDS)
        return result
    elif r.status_code == 400:
        ee_result = r.json()
        raise exception(ee_result['error'])
    elif r.status_code == 404:
        raise exception(
            _('The url "{}" couldn’t be found').format(url)
        )
    else:
        raise UnknownMapitException(
            _('Unknown error for "{0}"').format(
                url
            )
        )


def get_areas_from_postcode(original_postcode):
    postcode = re.sub(r'(?ms)\s*', '', original_postcode.lower())
    if re.search(r'[^a-z0-9]', postcode):
        raise BadPostcodeException(
            _('There were disallowed characters in "{0}"').format(
                original_postcode)
        )
    cache_key = 'mapit-postcode:' + postcode
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    url = "{0}/api/elections/?postcode={1}".format(
        EE_URL_BASE, urlquote(postcode))
    return get_areas(url, cache_key, BadPostcodeException)


def get_areas_from_coords(coords):
    url = "{0}/api/elections/?coords={1}".format(
        EE_URL_BASE, urlquote(coords))

    cache_key = 'mapit-postcode:' + coords
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    return get_areas(url, cache_key, BadCoordinatesException)
