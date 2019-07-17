from datetime import datetime

from django.db.models import Count

from candidates.models import Ballot


def get_attention_needed_posts():
    now = datetime.now()
    qs = Ballot.objects.filter(election__current=True)
    qs = qs.select_related("election", "post")
    qs = qs.annotate(count=Count("membership"))
    qs = qs.order_by("count", "election__name", "post__label")
    return qs
