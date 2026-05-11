from urllib.parse import urlunsplit

from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.syndication.views import Feed, add_domain
from django.core.paginator import Paginator
from django.utils.feedgenerator import Atom1Feed

from .models import ResultEvent

PAGE_SIZE = 300


class RFC5005PagingMixin:
    """
    Mixin adding RFC 5005 (Feed Paging and Archiving) support.

    Adds first/last/next/previous link elements to the feed root and
    slices the queryset to PAGE_SIZE items per page, selected via ?page=N.
    """

    page_size = PAGE_SIZE

    def get_object(self, request, *args, **kwargs):
        try:
            page_number = max(1, int(request.GET.get("page", 1)))
        except (ValueError, TypeError):
            page_number = 1
        paginator = Paginator(self._base_queryset(), self.page_size)
        return paginator.get_page(page_number)

    def _base_queryset(self):
        return (
            ResultEvent.objects.filter(election__current=True)
            .select_related("user")
            .select_related("election")
            .select_related("post")
            .select_related("winner")
            .select_related("winner_party")
            .select_related("winner__image")
            .order_by("-created")
        )

    def items(self, page_obj):
        return page_obj

    def get_feed(self, obj, request):
        feed = super().get_feed(obj, request)
        page_obj = obj
        base_url = add_domain(
            Site.objects.get_current().domain, request.path, request.is_secure()
        )

        feed.feed["feed_url"] = f"{base_url}?page={page_obj.number}"

        paging_links = [
            ("first", f"{base_url}?page=1"),
            ("last", f"{base_url}?page={page_obj.paginator.num_pages}"),
        ]
        if page_obj.has_previous():
            paging_links.append(
                (
                    "previous",
                    f"{base_url}?page={page_obj.previous_page_number()}",
                )
            )
        if page_obj.has_next():
            paging_links.append(
                ("next", f"{base_url}?page={page_obj.next_page_number()}")
            )
        feed.feed["paging_links"] = paging_links
        return feed


class PagingAtom1Feed(Atom1Feed):
    def add_root_elements(self, handler):
        super().add_root_elements(handler)
        for rel, href in self.feed.get("paging_links", []):
            handler.addQuickElement("link", "", {"rel": rel, "href": href})


class BasicResultEventsFeed(RFC5005PagingMixin, Feed):
    feed_type = PagingAtom1Feed
    title = "Election results from {site_name}".format(
        site_name=settings.SITE_NAME
    )
    link = "/"
    description = "A basic feed of election results"

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
        return "/#{}".format(item.id)

    def item_updateddate(self, item):
        return item.created

    def item_pubdate(self, item):
        return item.created

    def item_author_name(self, item):
        if item.user:
            return item.user.username
        return "unknown"


class ResultEventsAtomFeedGenerator(PagingAtom1Feed):
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
