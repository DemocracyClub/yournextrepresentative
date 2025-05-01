import contextlib
import re
from typing import Optional

from django.contrib.admin.utils import NestedObjects
from django.contrib.postgres.search import TrigramSimilarity
from django.core.management import BaseCommand
from django.db import transaction
from popolo.models import Post


class Command(BaseCommand):
    def guess_replacement_post(self, post) -> Optional[Post]:
        def guess(post, related_obj, object_attr="posts", exclude_kwargs=None):
            print(f"Guessing for post {post.pk} and {related_obj}")
            # special case PCCs
            if "Police and Crime Commissioner for " in post.label:
                return (
                    Post.objects.filter(
                        elections__slug__startswith=f"pcc.{post.slug}"
                    )
                    .filter(created__gt=post.created)
                    .order_by("-created")
                    .first()
                )
            # Special case Mayors
            if "Mayor" in post.label:
                return (
                    Post.objects.filter(
                        elections__slug__startswith=f"mayor.{post.slug}"
                    )
                    .filter(created__gt=post.created)
                    .order_by("-created")
                    .first()
                )

            # Special case gla.a
            if "Assembly" in post.label and post.slug == "gla":
                return (
                    Post.objects.filter(elections__slug__startswith="gla.a.")
                    .filter(created__gt=post.created)
                    .order_by("-created")
                    .first()
                )
            # Special case naw.a

            if (
                "Assembly" in post.label
                and post.identifier
                and post.identifier.startswith("gss:W0")
            ):
                return (
                    Post.objects.filter(elections__slug__startswith="naw.a.")
                    .filter(created__gt=post.created)
                    .order_by("-created")
                    .first()
                )

            label = post.label
            label = label.replace("Member of Parliament for ", "")
            label = label.replace("Member of the Scottish Parliament for ", "")
            label = label.replace("Assembly Member for ", "")
            label = re.sub(
                r"\bward\b$", "", label, flags=re.IGNORECASE
            ).rstrip()
            qs = getattr(related_obj, object_attr).exclude(pk=post.pk)
            if exclude_kwargs:
                qs = qs.exclude(**exclude_kwargs)

            try:
                print(f"Finding an exact match for {label}")
                return qs.filter(
                    label=label,
                ).get()
            except Post.DoesNotExist:
                print("Exact match not found, trying trigram")
                matches = (
                    qs.annotate(sim=TrigramSimilarity("label", label))
                    .filter(sim__gt=0.6)
                    .exclude(pk=post.pk)
                )
                if matches.count() > 1:
                    print("more than one match found")
                    raise ValueError(
                        f"Too many results {matches.values('label', 'sim')}"
                    )
                print("At most one match found")
                with contextlib.suppress(post.DoesNotExist):
                    return matches.get()
            except post.MultipleObjectsReturned:
                print(f"more than one post matches {label}")
                return (
                    qs.filter(
                        label=label,
                    )
                    .filter(created__gt=post.created)
                    .order_by("-created")
                    .first()
                )

        if post.resultevent_set.exists():
            with contextlib.suppress(ValueError):
                guessed = guess(post, post.resultevent_set.first().election)
                if guessed:
                    return guessed
        org_qs = post.organization.posts.exclude(ballot=None)
        if org_qs.exists():
            print("Guessing based on Org")
            with contextlib.suppress(ValueError):
                return guess(
                    post, post.organization, exclude_kwargs={"ballot": None}
                )
        print("no guess")
        return None

    @transaction.atomic
    def handle(self, *args, **options):
        qs = Post.objects.filter(ballot=None)

        for post in qs:
            # We can remove PostIdentifiers relating to this Post
            post.postidentifier_set.all().delete()

            # Set related Membership IDs to None (Membership->Post FK is deprecated)
            for membership in post.memberships.all():
                membership.post = None
                membership.save()

            replacement_post = self.guess_replacement_post(post)

            # Attempt to move ResultEvent objects to the correct post
            for resultevent in post.resultevent_set.all():
                if not replacement_post:
                    import ipdb

                    ipdb.set_trace()

                    raise ValueError(
                        "Post has resultevent, but no replacement guess found"
                    )
                resultevent.post = replacement_post
                resultevent.save()

            for loggedaction in post.loggedaction_set.all():
                if not replacement_post:
                    import ipdb

                    ipdb.set_trace()
                    raise ValueError(
                        "Post has loggedaction, but no replacement guess found"
                    )

                loggedaction.post = replacement_post
                loggedaction.save()

            collector = NestedObjects(using="default")
            collector.collect([post])
            collected = collector.nested()
            if len(collected) > 1:
                print(post.pk)
                print(collected)
                raise ValueError(f"Object has related objects: {collected}")

        raise ValueError()
