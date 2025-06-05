import contextlib
import re
from typing import Optional

from django.contrib.admin.utils import NestedObjects
from django.contrib.postgres.search import TrigramSimilarity
from django.core.management import BaseCommand
from django.db import transaction
from popolo.models import Post


class Command(BaseCommand):
    help = """
    A command to delete orphan posts in the database.

    There are three categories of posts:
    1. True orphan posts: no related objects at all.
    2. Posts with related objects for which we're able to guess a replacement.
    3. Posts with related objects for which we weren't able to guess a replacement.

    The base command will only delete true orphan posts.

    Passing --with-repl will also delete the second category and move their related objects to the replacement.
"""

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry-run",
            help="Do not delete any objects, just print what would be deleted.",
        )
        parser.add_argument(
            "--with-repl",
            action="store_true",
            dest="with-repl",
            help="Also delete posts with related objects where we've been able to guess a replacement.",
        )

    def guess_replacement_post(self, post) -> Optional[Post]:
        def guess(post, related_obj, object_attr="posts", exclude_kwargs=None):
            self.stdout.write(
                f"Guessing replacement for post {post.pk} ({post.label}) using {related_obj}"
            )
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
                return qs.filter(label=label).get()
            except Post.DoesNotExist:
                self.stdout.write(
                    f"Failed to find an exact match for {label}, trying trigram similarity"
                )
                matches = (
                    qs.annotate(sim=TrigramSimilarity("label", label))
                    .filter(sim__gt=0.6)
                    .exclude(pk=post.pk)
                )
                if matches.exists():
                    self.stdout.write("Is it one of these?")
                    for i, match in enumerate(matches, start=1):
                        self.stdout.write(f"\t {i}. {match.label}")

                    return self.prompt_user_for_match(matches)
            except Post.MultipleObjectsReturned:
                self.stdout.write(f"More than one post matches {label}")
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
        return None

    def prompt_user_for_match(self, matches):
        user_input = None
        while not user_input:
            user_input = input("Pick a number to match or enter 's' to skip: ")
            if user_input == "s":
                return None
            if user_input.isdigit() and 1 <= int(user_input) <= matches.count():
                user_choice = int(user_input)
            else:
                self.stdout.write("Invalid input, please try again")
                user_input = None

        match = matches[user_choice - 1]
        self.stdout.write(f"You picked {match.label}")
        return match

    def move_related_objects(self, post, replacement_post):
        # Attempt to move ResultEvent objects to the correct post
        for resultevent in post.resultevent_set.all():
            resultevent.post = replacement_post
            resultevent.save()

        # Attempt to move LoggedAction objects to the correct post
        for loggedaction in post.loggedaction_set.all():
            loggedaction.post = replacement_post
            loggedaction.save()

    def check_for_related_objects(self, post):
        collector = NestedObjects(using="default")
        collector.collect([post])
        collected = collector.nested()
        if len(collected) > 1:
            raise ValueError(f"Post {post.pk} has related objects: {collected}")

    @transaction.atomic
    def delete_orphan_posts(self, posts):
        for post in posts:
            self.delete_post(post)

    @transaction.atomic
    def delete_posts_with_replacements(self, posts):
        for post, replacement_post in posts:
            self.move_related_objects(post, replacement_post)
            self.delete_post(post)

    def delete_post(self, post):
        # We can remove PostIdentifiers relating to this Post
        post.postidentifier_set.all().delete()

        # Set related Membership IDs to None (Membership->Post FK is deprecated)
        for membership in post.memberships.all():
            membership.post = None
            membership.save()

        # Check we didn't miss any related objects before deleting post
        self.check_for_related_objects(post)
        post.delete()

    def handle(self, *args, **options):
        qs = Post.objects.filter(ballot=None)
        self.stdout.write(f"Found {qs.count()} orphan posts")
        if options["dry-run"]:
            self.stdout.write("Dry run, not deleting anything")

        true_orphan_posts = []
        posts_with_replacements = []
        posts_with_no_replacements = []

        for post in qs:
            if post.loggedaction_set.exists() or post.resultevent_set.exists():
                repl_post = None
                repl_post = self.guess_replacement_post(post)

                if not repl_post:
                    posts_with_no_replacements.append(post)
                    continue

                posts_with_replacements.append((post, repl_post))
            else:
                true_orphan_posts.append(post)

            if options["dry-run"] and options["with-repl"]:
                if post.loggedaction_set.exists():
                    self.stdout.write(
                        f"Would move {post.loggedaction_set.count()} LoggedActions from Post {post.pk} ({post.label}) to replacement {repl_post.pk} ({repl_post.label})"
                    )
                if post.resultevent_set.exists():
                    self.stdout.write(
                        f"Would move {post.resultevent_set.count()} ResultEvents from Post {post.pk} ({post.label}) to replacement {repl_post.pk} ({repl_post.label})"
                    )

        for post in posts_with_no_replacements:
            self.stderr.write(
                f"Failed to find replacement Post for objects related to {post.pk} ({post.label}), please check manually."
            )

        if options["dry-run"]:
            self.stdout.write(
                f"Would delete {len(true_orphan_posts)} true orphan posts"
            )
            if options["with-repl"]:
                self.stdout.write(
                    f"Would delete {len(posts_with_replacements)} posts with replacements"
                )
        else:
            self.delete_orphan_posts(true_orphan_posts)
            if options["with-repl"]:
                self.delete_posts_with_replacements(posts_with_replacements)
