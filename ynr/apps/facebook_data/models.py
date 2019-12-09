from dateutil.parser import parse
from django.contrib.postgres.fields.jsonb import JSONField
from django.db import models


def advert_image_path(instance, filename):
    # Upload images in a directory per person
    return "images/facebook_adverts/{0}/{1}".format(
        instance.person_id, filename
    )


class FacebookAdvert(models.Model):
    """
    A Facebook Advert, as described in the Facebook Ad Library

    https://www.facebook.com/ads/library/

    """

    ad_id = models.CharField(
        max_length=500, help_text="The Facebook ID for this advert"
    )
    ad_json = JSONField(
        help_text="The JSON returned from the Facebook "
        "Graph API for this advert"
    )
    person = models.ForeignKey("people.Person", on_delete=models.CASCADE)
    associated_url = models.CharField(
        max_length=800,
        blank=True,
        help_text="The URL used to import the data – useful "
        "for being able to remove incorrect adverts"
        "for a person without re-importing every advert for them",
    )
    image = models.ImageField(
        upload_to=advert_image_path,
        max_length=512,
        blank=True,
        help_text="A screenshot of the rendered advert",
    )

    class Meta:
        ordering = ("-ad_json__ad_delivery_start_time",)
        get_latest_by = "ad_json__ad_delivery_start_time"

    @property
    def get_spend_range(self):
        return sorted(self.ad_json.get("spend").values())

    @property
    def get_impressions_range(self):
        return sorted(self.ad_json.get("impressions").values())

    @property
    def get_funding_entity(self):
        return self.ad_json.get("funding_entity")

    def _get_impressions_for_gender(self, gender):
        demographic_distribution = self.ad_json.get("demographic_distribution")
        return round(
            sum(
                [
                    float(x["percentage"])
                    for x in demographic_distribution
                    if x["gender"] == gender
                ]
            )
            * 100,
            2,
        )

    @property
    def get_female_impressions(self):
        return self._get_impressions_for_gender("female")

    @property
    def get_male_impressions(self):
        return self._get_impressions_for_gender("male")

    def _get_date(self, field):
        return parse(self.ad_json.get(field))

    @property
    def stop_date(self):
        return self._get_date("ad_delivery_stop_time")

    @property
    def start_date(self):
        return self._get_date("ad_delivery_start_time")
