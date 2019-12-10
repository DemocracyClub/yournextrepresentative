from django_filters import filterset, filters

from facebook_data.models import FacebookAdvert


class FacebookAdvertFilterSet(filterset.FilterSet):
    class Meta:
        model = FacebookAdvert
        fields = ["person_id"]

    person_id = filters.Filter(
        field_name="person_id",
        label="Person ID",
        help_text="The person who's page ran the advert",
    )
