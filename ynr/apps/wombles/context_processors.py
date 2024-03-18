import datetime

from candidates.models import LoggedAction
from django.core.cache import cache
from django.db.models import Count
from django.utils import timezone


def action_counts_processor(request):
    # Only proceed if user is authenticated
    if request.user.is_authenticated:
        cache_key = f"user_{request.user.id}_action_counts"
        # Try to get cached data
        action_counts = cache.get(cache_key)

        if action_counts is None:
            # Query the LoggedAction model for counts of each ActionType
            actions = (
                LoggedAction.objects.filter(user=request.user)
                .values("action_type")
                .annotate(count=Count("action_type"))
            )
            action_counts = {
                action["action_type"].replace("-", "_"): action["count"]
                for action in actions
            }
            action_counts["total_actions"] = LoggedAction.objects.filter(
                user=request.user
            ).count()

            one_month_ago = timezone.now() - datetime.timedelta(days=30)
            action_counts["last_months_actions"] = LoggedAction.objects.filter(
                user=request.user, created__gte=one_month_ago
            ).count()

            # Cache the result for an hour
            cache.set(cache_key, action_counts, 3600)

        return {"action_counts": action_counts}
    return {}
