from rest_framework import serializers

from popolo import models as popolo_models

# These are serializer classes from the Django-REST-framework API
#
# For most objects there are two serializers - a full one and a
# minimal one.  The minimal ones (whose class names begin 'Minimal')
# are used for serializing the objects when they're just being
# included as related objects, rather than the resource that
# information is being requested about.
#
# e.g. if you request information about a Post via the 'posts'
# endpoint, it's pretty useful to have the ID, URL and name of the
# elections that the Post is part of, but you probably don't need
# every bit of election metadata.  A request to the 'elections'
# endpoint, however, would include full metadata about the elections.
#
# This reduces the bloat of API responses, at the cost of some users
# having to make extra queries.


class OrganizationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = popolo_models.Organization
        fields = ("url", "name", "slug", "last_updated", "created")

    url = serializers.HyperlinkedIdentityField(
        view_name="organization-detail",
        lookup_field="slug",
        lookup_url_kwarg="slug",
    )
    last_updated = serializers.DateTimeField(source="modified")
