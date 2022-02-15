from urllib.parse import urlunsplit

from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed

from .models import ResultEvent


class BasicResultEventsFeed(Feed):
    feed_type = Atom1Feed
    title = "Election results from {site_name}".format(
        site_name=settings.SITE_NAME
    )
    link = "/"
    description = "A basic feed of election results"

    def items(self):
        return (
            ResultEvent.objects.filter(election__current=True)
            .select_related("user")
            .select_related("election")
            .select_related("post")
            .select_related("winner")
            .select_related("winner_party")
            .select_related("winner__image")
        )

    def item_title(self, item):
        if item.retraction:
            msg = "Correction: retracting the statement that {name} ({party}) won in {cons}"

        else:
            msg = "{name} ({party}) won in {cons}"
        return msg.format(
            name=item.winner.name,
            party=item.winner_party.name,
            cons=item.short_post_name,
        )

    def item_description(self, item):
        if item.retraction:
            message = (
                "At {datetime}, a {site_name} volunteer retracted the "
                "previous assertion that {name} ({party}) won the "
                "ballot in {cons}, quoting the source '{source}'."
            )

        else:
            message = (
                "A {site_name} volunteer recorded at {datetime} that "
                "{name} ({party}) won the ballot in {cons}, quoting "
                "the source '{source}'."
            )
        return message.format(
            name=item.winner.name,
            datetime=item.created.strftime("%Y-%m-%d %H:%M:%S"),
            party=item.winner_party.name,
            cons=item.short_post_name,
            source=item.source,
            site_name=Site.objects.get_current().name,
        )

    def item_link(self, item):
        # Assuming we're only going to show these events on the front
        # page for the moment:
        return "/#{}".format(item.id)

    def item_updateddate(self, item):
        return item.created

    def item_pubdate(self, item):
        return item.created

    def item_author_name(self, item):
        if item.user:
            return item.user.username
        return "unknown"


class ResultEventsAtomFeedGenerator(Atom1Feed):
    def add_item_elements(self, handler, item):
        super().add_item_elements(handler, item)
        keys = [
            "retraction",
            "election_slug",
            "election_name",
            "election_date",
            "post_id",
            "winner_person_id",
            "winner_person_name",
            "winner_party_id",
            "winner_party_name",
            "user_id",
            "post_name",
            "information_source",
        ]
        for k in ["image_url", "parlparse_id"]:
            if item[k]:
                keys.append(k)
        for k in keys:
            handler.addQuickElement(k, str(item[k]))


class ResultEventsFeed(BasicResultEventsFeed):
    feed_type = ResultEventsAtomFeedGenerator
    title = "Election results from {site_name} (with extra data)".format(
        site_name=settings.SITE_NAME
    )
    description = (
        "A feed of results from the UK 2015 General Election (with extra data)"
    )

    def item_extra_kwargs(self, o):
        user_id = None
        if o.user:
            user_id = o.user.id
        image_url = o.image_url_path
        if image_url:
            # FIXME: this is just assuming 'https' as the protocol and
            # that the current site has a correct domain at the moment,
            # since this class doesn't have access to the request object.
            image_url = urlunsplit(
                ("https", Site.objects.get_current().domain, image_url, "", "")
            )
        return {
            "retraction": int(o.retraction),
            "election_slug": o.election.slug,
            "election_name": o.election.name,
            "election_date": o.election.election_date,
            "post_id": o.post.slug if o.post else o.old_post_id,
            "winner_person_id": o.winner.id,
            "winner_person_name": o.winner.name,
            "winner_party_id": o.winner_party.legacy_slug,
            "winner_party_name": o.winner_party.name,
            "user_id": user_id,
            "post_name": o.short_post_name,
            "information_source": o.source,
            "image_url": image_url,
            "parlparse_id": o.parlparse_id,
        }
