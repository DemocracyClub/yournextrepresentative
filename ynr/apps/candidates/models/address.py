from collections import defaultdict

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.six.moves.urllib_parse import urljoin
from django.utils.text import slugify
from django.utils.translation import ugettext as _

from pygeocoder import Geocoder, GeocoderError
import requests

from elections.models import Election

# We use this both for validation of address and the results of the
# lookup, so the MapIt and geocoder lookups should be cached so we
# don't make double requests:


def check_address(address_string, country=None):
    tidied_address_before_country = address_string.strip()
    if country is None:
        tidied_address = tidied_address_before_country
    else:
        tidied_address = tidied_address_before_country + ", " + country
    try:
        location_results = Geocoder.geocode(tidied_address)
    except GeocoderError:
        message = _("Failed to find a location for '{0}'")
        raise ValidationError(message.format(tidied_address_before_country))
    lat, lon = location_results[0].coordinates
    all_mapit_json = []
    queries_to_try = defaultdict(set)
    for election in Election.objects.current().prefetch_related("area_types"):
        area_types = election.area_types.values_list("name", flat=True)
        queries_to_try[election.area_generation].update(area_types)
    for area_generation, area_types in queries_to_try.items():
        mapit_lookup_url = urljoin(
            settings.MAPIT_BASE_URL,
            "point/4326/{lon},{lat}".format(lon=lon, lat=lat),
        )
        mapit_lookup_url += "?type=" + ",".join(area_types)
        mapit_lookup_url += "&generation={}".format(election.area_generation)
        mapit_result = requests.get(
            mapit_lookup_url, headers={"User-Agent": "scraper/sym"}
        )
        mapit_json = mapit_result.json()
        if "error" in mapit_json:
            message = _("The area lookup returned an error: '{error}'")
            raise ValidationError(message.format(error=mapit_json["error"]))
        all_mapit_json += mapit_json.items()
    sorted_mapit_results = sorted(
        all_mapit_json, key=lambda t: (t[1]["type"], int(t[0]))
    )
    if not sorted_mapit_results:
        message = _(
            "The address '{0}' appears to be outside the area this site knows about"
        )
        raise ValidationError(message.format(tidied_address_before_country))
    types_and_areas = [
        {"area_type_code": a[1]["type"], "area_id": a[0]}
        for a in sorted_mapit_results
    ]
    if settings.AREAS_TO_ALWAYS_RETURN:
        types_and_areas += settings.AREAS_TO_ALWAYS_RETURN
    types_and_areas_joined = ",".join(
        "{area_type_code}--{area_id}".format(**ta) for ta in types_and_areas
    )
    area_slugs = [slugify(a[1]["name"]) for a in sorted_mapit_results]
    ignored_slug = "-".join(area_slugs)
    return {
        "type_and_area_ids": types_and_areas_joined,
        "ignored_slug": ignored_slug,
    }
