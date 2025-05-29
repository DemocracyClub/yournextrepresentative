import contextlib
import re
from typing import Optional

from django.contrib.admin.utils import NestedObjects
from django.contrib.postgres.search import TrigramSimilarity
from django.core.management import BaseCommand
from django.db import transaction
from popolo.models import Post


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry-run",
            help="Do not delete any objects, just print what would be deleted.",
        )

    def guess_replacement_post(self, post) -> Optional[Post]:
        def guess(post, related_obj, object_attr="posts", exclude_kwargs=None):
            self.stdout.write(f"Guessing for post {post.pk} and {related_obj}")
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

            label = post.label
            label = label.replace("Member of Parliament for ", "")
            label = label.replace("Member of the Scottish Parliament for ", "")
            label = label.replace("Assembly Member for ", "")
            label = label.replace("Member of the Legislative Assembly for ", "")
            label = re.sub(
                r"\bward\b$", "", label, flags=re.IGNORECASE
            ).rstrip()
            qs = getattr(related_obj, object_attr).exclude(pk=post.pk)
            if exclude_kwargs:
                qs = qs.exclude(**exclude_kwargs)

            try:
                self.stdout.write(f"Finding an exact match for {label}")
                return qs.filter(
                    label=label,
                ).get()
            except Post.DoesNotExist:
                self.stdout.write("Exact match not found, trying trigram")
                matches = (
                    qs.annotate(sim=TrigramSimilarity("label", label))
                    .filter(sim__gt=0.6)
                    .exclude(pk=post.pk)
                )
                if matches.count() > 1:
                    self.stdout.write("more than one match found")
                    raise ValueError(
                        f"Too many results {matches.values('label', 'sim')}"
                    )
                self.stdout.write("At most one match found")
                with contextlib.suppress(post.DoesNotExist):
                    return matches.get()
            except post.MultipleObjectsReturned:
                self.stdout.write(f"more than one post matches {label}")
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
            self.stdout.write("Guessing based on Org")
            with contextlib.suppress(ValueError):
                return guess(
                    post, post.organization, exclude_kwargs={"ballot": None}
                )
        self.stdout.write("no guess")
        return None

    @transaction.atomic
    def handle(self, *args, **options):
        qs = Post.objects.filter(ballot=None)
        self.stdout.write(f"Found {qs.count()} orphan posts")
        if options["dry-run"]:
            self.stdout.write("Dry run, not deleting anything")

        posts_with_no_replacement = []

        for post in qs:
            if not options["dry-run"]:
                # We can remove PostIdentifiers relating to this Post
                post.postidentifier_set.all().delete()

                # Set related Membership IDs to None (Membership->Post FK is deprecated)
                for membership in post.memberships.all():
                    membership.post = None
                    membership.save()

            replacement_post = self.guess_replacement_post(post)
            replacement_failed = False

            # Attempt to move ResultEvent objects to the correct post
            for resultevent in post.resultevent_set.all():
                if not replacement_post:
                    self.stderr.write(
                        f"{post.pk} has resultevent, but no replacement guess found"
                    )
                    replacement_failed = True
                    continue
                if not options["dry-run"]:
                    resultevent.post = replacement_post
                    resultevent.save()

            # Attempt to move LoggedAction objects to the correct post
            for loggedaction in post.loggedaction_set.all():
                if not replacement_post:
                    self.stderr.write(
                        f"{post.pk}: post has loggedaction, but no replacement guess found"
                    )
                    replacement_failed = True
                    continue
                if not options["dry-run"]:
                    loggedaction.post = replacement_post
                    loggedaction.save()

            if options["dry-run"] and replacement_post:
                if post.loggedaction_set.exists():
                    self.stdout.write(
                        f"Would move {post.loggedaction_set.count()} LoggedActions from Post {post.pk} to replacement {replacement_post.pk}"
                    )
                if post.resultevent_set.exists():
                    self.stdout.write(
                        f"Would move {post.resultevent_set.count()} ResultEvents from Post {post.pk} to replacement {replacement_post.pk}"
                    )

            if replacement_failed:
                posts_with_no_replacement.append(post)
                continue

            if not options["dry-run"]:
                # Check we didn't miss any related objects before deleting post
                collector = NestedObjects(using="default")
                collector.collect([post])
                collected = collector.nested()
                if len(collected) > 1:
                    raise ValueError(
                        f"Post {post.pk} has related objects: {collected}"
                    )

                self.stdout.write(f"Deleting post {post.pk}")
                post.delete()

        for post in posts_with_no_replacement:
            self.stderr.write(
                f"Failed to find replacement Post for objects related to {post.pk} ({post.label}), please check manually."
            )
