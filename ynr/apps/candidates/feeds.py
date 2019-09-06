import re

from django.contrib.syndication.views import Feed
from django.urls import reverse
from django.utils.feedgenerator import Atom1Feed
from django.conf import settings

from .models import LoggedAction

lock_re = re.compile(r"^(?:Unl|L)ocked\s*constituency (.*) \((\d+)\)$")


class ChangesMixin(object):
    def get_title(self, logged_action):
        if logged_action.person:
            return "{} ({}) - {}".format(
                logged_action.person.name,
                logged_action.person_id,
                logged_action.action_type,
            )
        elif logged_action.post:
            return "{} ({}) - {}".format(
                logged_action.post.label,
                logged_action.post.slug,
                logged_action.action_type,
            )
        else:
            return logged_action.action_type

    def get_guid(self, logged_action):
        return self.id_format(logged_action.id)

    def get_updated(self, logged_action):
        # Note that we're using the created attribute rather than
        # updated, since any save() of the LoggedAction will cause
        # updated to be set to now, but the item won't really have
        # changed in a sense that means we'd want it to appear again
        # in an RSS feed.
        return logged_action.created

    def get_author(self, logged_action):
        if logged_action.user:
            return logged_action.user.username
        else:
            return "Automated change"


class RecentChangesFeed(ChangesMixin, Feed):
    site_name = settings.SITE_NAME
    title = "{site_name} recent changes".format(site_name=site_name)
    description = "Changes to {site_name} candidates".format(
        site_name=site_name
    )
    link = "/feeds/changes.xml"
    feed_type = Atom1Feed
    id_format = "changes:{0}"

    def items(self):
        return LoggedAction.objects.order_by("-updated")[:50]

    def item_title(self, item):
        return self.get_title(item)

    def item_description(self, item):
        updated = "Updated at {0}".format(str(item.updated))
        description = "{}\n\n{}\n".format(item.source, updated)

        return description

    def item_guid(self, item):
        return self.id_format.format(item.id)

    def item_updateddate(self, item):
        return self.get_updated(item)

    def item_author_name(self, item):
        return self.get_author(item)

    def item_link(self, item):
        # As a hack for the moment, constituencies are just mentioned
        # in the source message:
        if item.person_id:
            return reverse("person-view", args=[item.person_id])
        else:
            return "/"


class NeedsReviewFeed(ChangesMixin, Feed):
    site_name = settings.SITE_NAME
    title = "{site_name} changes for review".format(site_name=site_name)
    link = "/feeds/needs-review.xml"
    feed_type = Atom1Feed
    id_format = "needs-review:{0}"

    def items(self):
        # Consider changes in the last 5 days. We exclude any photo
        # related activity since that has its own reviewing system.
        return (
            LoggedAction.objects.exclude(action_type__startswith="photo-")
            .in_recent_days(1)
            .order_by("-created")
            .needs_review()
        )

    def item_title(self, item):
        return self.get_title(item)

    def item_guid(self, item):
        return self.id_format.format(item.id)

    def item_updateddate(self, item):
        return self.get_updated(item)

    def item_author_name(self, item):
        return self.get_author(item)

    def item_description(self, item):
        la = item
        return """
<p>{action_type} of {subject} by {user} with source: “ {source} ”;</p>
<ul>
{reasons_review_needed}
</ul></p>{diff}""".strip().format(
            action_type=la.action_type,
            subject=la.subject_html,
            user=la.user.username,
            source=la.source,
            reasons_review_needed=item.flagged_reason,
            timestamp=la.updated,
            diff=la.diff_html,
        )

    def item_link(self, item):
        return item.subject_url
