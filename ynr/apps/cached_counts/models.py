from candidates.models import Ballot
from django.db.models import Count


def get_attention_needed_posts():
    qs = Ballot.objects.current_or_future()
    qs = qs.select_related("election", "post")
    qs = qs.annotate(count=Count("membership"))
    return qs.order_by("count", "election__name", "post__label")
