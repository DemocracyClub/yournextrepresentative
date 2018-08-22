from datetime import datetime

from django.db.models import Count

from candidates.models import PostExtraElection


def get_attention_needed_posts():
    now = datetime.now()
    qs = PostExtraElection.objects.filter(election__current=True)
    qs = qs.select_related("election", "postextra__base")
    qs = qs.annotate(count=Count("membership"))
    qs = qs.order_by("count", "election__name", "postextra__base__label")
    return qs
