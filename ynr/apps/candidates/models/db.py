from collections import defaultdict
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.db import models
from django.db.models.signals import post_save
from django.utils.html import escape
from django.utils.six import text_type


from moderation_queue.review_required_helper import REVIEW_TYPES


def merge_dicts_with_list_values(dict_a, dict_b):
    return {
        k: dict_a.get(k, []) + dict_b.get(k, [])
        for k in set(dict_a.keys()) | set(dict_b.keys())
    }


class LoggedActionQuerySet(models.QuerySet):
    def in_recent_days(self, days=5):
        return self.filter(created__gte=(datetime.now() - timedelta(days=days)))

    def needs_review(self):
        return self.exclude(flagged_type="").order_by("-created")


class LoggedAction(models.Model):
    """A model for logging the actions of users on the site

    We record the changes that have been made to a person in PopIt in
    that person's 'versions' field, but is not much help for queries
    like "what has John Q User been doing on the site?". The
    LoggedAction model makes that kind of query easy, however, and
    should be helpful in tracking down both bugs and the actions of
    malicious users."""

    user = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.CASCADE
    )
    person = models.ForeignKey(
        "people.Person", blank=True, null=True, on_delete=models.CASCADE
    )
    action_type = models.CharField(max_length=64)
    popit_person_new_version = models.CharField(max_length=32)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True)
    ip_address = models.CharField(max_length=50, blank=True, null=True)
    source = models.TextField()
    post = models.ForeignKey(
        "popolo.Post", blank=True, null=True, on_delete=models.CASCADE
    )
    ballot = models.ForeignKey(
        "candidates.Ballot", null=True, on_delete=models.CASCADE
    )

    flagged_type = models.CharField(
        max_length=100,
        blank=True,
        null=False,
        help_text="If NOT NULL, a type of flag that marks "
        "this edit as needing review by a human",
    )
    flagged_reason = models.CharField(
        max_length=255,
        blank=True,
        null=False,
        help_text="An explaination of the reason for flagging this edit",
    )

    objects = LoggedActionQuerySet.as_manager()

    def __str__(self):
        return "username='{username}' action_type='{action_type}'".format(
            username=self.user.username, action_type=self.action_type
        )

    @property
    def ballot_guess(self):
        """
        FIXME: Note that this won't always be correct because
        LoggedAction objects only reference Post at the moment,
        rather than a Post and an Election (or a Ballot).
        """
        from candidates.models import Ballot

        if self.post:
            election = self.post.elections.order_by("-current").first()
            return Ballot.objects.get(election=election, post=self.post)

    @property
    def subject_url(self):
        ballot = self.ballot_guess
        if ballot:
            return ballot.get_absolute_url()
        elif self.person:
            return reverse("person-view", kwargs={"person_id": self.person.id})
        return "/"

    @property
    def subject_html(self):
        ballot = self.ballot_guess
        if ballot:
            return '<a href="{url}">{text} ({post_slug})</a>'.format(
                url=self.subject_url,
                text=ballot.post.short_label,
                post_slug=ballot.post.slug,
            )
        elif self.person:
            return '<a href="{url}">{text} ({person_id})</a>'.format(
                url=self.subject_url,
                text=self.person.name,
                person_id=self.person.id,
            )
        return ""

    @property
    def diff_html(self):
        from popolo.models import VersionNotFound

        if not self.person:
            return ""
        try:
            return self.person.diff_for_version(
                self.popit_person_new_version, inline_style=True
            )
        except VersionNotFound as e:
            return "<p>{}</p>".format(escape(text_type(e)))

    def set_review_required(self):
        """
        Runs all `ReviewRequiredDecider` classed over a LoggedAction
        and sets the flags accordingly

        """

        for review_type in REVIEW_TYPES:
            decider = review_type.cls(self)
            decision = decider.needs_review()
            if decision == review_type.cls.Status.NEEDS_REVIEW:
                self.flagged_type = review_type.type
                self.flagged_reason = decider.review_description_text()
                break
            if decision == review_type.cls.Status.NO_REVIEW_NEEDED:
                break

    def save(self, **kwargs):
        self.set_review_required()
        return super().save(**kwargs)


class PersonRedirect(models.Model):
    """This represents a redirection from one person ID to another

    This is typically used to redirect from the person that is deleted
    after two people are merged"""

    old_person_id = models.IntegerField()
    new_person_id = models.IntegerField()

    @classmethod
    def all_redirects_dict(cls):
        new_to_sorted_old = defaultdict(list)
        for old, new in cls.objects.values_list(
            "old_person_id", "new_person_id"
        ):
            new_to_sorted_old[new].append(old)
            new_to_sorted_old[new].sort()
        return new_to_sorted_old


class UserTermsAgreement(models.Model):
    user = models.OneToOneField(
        User, related_name="terms_agreement", on_delete=models.CASCADE
    )
    assigned_to_dc = models.BooleanField(default=False)


def create_user_terms_agreement(sender, instance, created, **kwargs):
    if created:
        UserTermsAgreement.objects.create(user=instance)


post_save.connect(create_user_terms_agreement, sender=User)
