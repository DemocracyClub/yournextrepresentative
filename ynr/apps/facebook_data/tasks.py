import http.cookiejar
import re
import sqlite3
import subprocess
import tempfile
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.core.files import File

from celery import shared_task
from facebook_data.models import FacebookAdvert
from people.models import PersonIdentifier


@shared_task(rate_limit="4/m")
def get_ads_for_page(person_id, page_id, page_url):
    if settings.RUNNING_TESTS:
        # Never run during tests
        return
    base_graph_url = "https://graph.facebook.com/v4.0/ads_archive"
    params = {
        "access_token": settings.FACEBOOK_TOKEN,
        "ad_reached_countries": ["GB"],
        "search_page_ids": page_id,
        "ad_active_status": "ALL",
        "fields": ",".join(
            [
                "ad_creation_time",
                "ad_creative_body",
                "ad_creative_link_caption",
                "ad_creative_link_description",
                "ad_creative_link_title",
                "ad_delivery_start_time",
                "ad_delivery_stop_time",
                "ad_snapshot_url",
                "currency",
                "demographic_distribution",
                "funding_entity",
                "impressions",
                "page_id",
                "page_name",
                "region_distribution",
                "spend",
            ]
        ),
    }
    next_url = "{}?{}".format(base_graph_url, urlencode(params, doseq=True))
    while next_url:
        req = requests.get(next_url)
        ad_data = req.json()
        next_url = ad_data.get("paging", {}).get("next")

        if not ad_data.get("data"):
            continue
        for ad in ad_data["data"]:
            ad_id = ad["ad_snapshot_url"].split("id=")[-1].split("&")[0]
            FacebookAdvert.objects.update_or_create(
                ad_id=ad_id,
                person_id=person_id,
                defaults={"ad_json": ad, "associated_url": page_url},
            )
    qs = FacebookAdvert.objects.filter(image="", person_id=person_id)
    if qs.exists():
        save_advert_image.delay(qs.latest().ad_id)


class FacebookExtractionError(ValueError):
    pass


class FacebookPageIDExtractor:
    def __init__(self, url):
        self.url = url
        self.extractors = [self.page_id_extractor, self.entity_id_extractor]
        self.session = self.get_session()

    def get_session(self):
        self.session = requests.Session()

        ff_cookie_path = getattr(settings, "FF_COOKIE_PATH", None)
        if ff_cookie_path:
            cj = http.cookiejar.CookieJar()
            con = sqlite3.connect(ff_cookie_path)
            cur = con.cursor()
            cur.execute(
                "SELECT host, path, isSecure, expiry, name, value FROM moz_cookies"
            )
            for item in cur.fetchall():
                c = http.cookiejar.Cookie(
                    0,
                    item[4],
                    item[5],
                    None,
                    False,
                    item[0],
                    item[0].startswith("."),
                    item[0].startswith("."),
                    item[1],
                    False,
                    item[2],
                    item[3],
                    item[3] == "",
                    None,
                    None,
                    {},
                )
                cj.set_cookie(c)
            self.session.cookies = cj
        return self.session

    def page_id_extractor(self, content):
        return re.search(r'{"pageID":"([\d]+)"', content)

    def entity_id_extractor(self, content):
        return re.search(r'"entity_id":"([\d]+)"', content)

    def extract(self):
        try:
            req = self.session.get(self.url)
            req.raise_for_status()
        except (requests.exceptions.RequestException,) as e:
            raise FacebookExtractionError(e)
        except:
            raise

        for extractor in self.extractors:
            match = extractor(req.text)
            if match:
                return match
        return None


@shared_task(rate_limit="4/m")
def extract_fb_page_id(idetifier_pk):
    if settings.RUNNING_TESTS:
        # Never run during tests
        return
    identifier = PersonIdentifier.objects.get(pk=idetifier_pk)
    extractor = FacebookPageIDExtractor(identifier.value)

    try:
        match = extractor.extract()
    except FacebookExtractionError as e:
        print("\t".join([str(identifier.person_id), identifier.value, str(e)]))
        return None

    if match:
        identifier.internal_identifier = int(match.group(1))
        identifier.save()
        get_ads_for_page.delay(
            identifier.person_id, identifier.internal_identifier
        )
    else:
        print("\t".join([str(identifier.person_id), identifier.value]))


@shared_task(rate_limit="10/m")
def save_advert_image(ad_id):
    if settings.RUNNING_TESTS:
        # Never run during tests
        return
    advert = FacebookAdvert.objects.filter(ad_id=ad_id).first()
    url = advert.ad_json["ad_snapshot_url"]
    url = url.split("access_token=")[0]
    url = "{}&access_token={}".format(url, settings.FACEBOOK_TOKEN)

    with tempfile.NamedTemporaryFile() as f:
        args = [
            "webkit2png",
            "-F",
            "-o",
            f.name,
            "--selector",
            "._8n-d",
            "--delay",
            "2",
            url,
        ]
        subprocess.call(args)
        saved_filename = "{}-full.png".format(f.name)

        advert.image.save(
            "{}.png".format(ad_id), File(open(saved_filename, "rb"))
        )
        advert.save()
