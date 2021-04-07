import hashlib
import datetime

from django.contrib.admin.utils import NestedObjects
from django.contrib.postgres.fields import JSONField
from django.db import connection, models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import mark_safe
from django.utils.functional import cached_property

from candidates.models.auth import TRUSTED_TO_LOCK_GROUP_NAME
from elections.models import Election


"""Extensions to the base django-popolo classes for YourNextRepresentative

These are done via explicit one-to-one fields to avoid the performance
problems with multi-table inheritance; it's preferable to state when you
want a join or not.

  http://stackoverflow.com/q/23466577/223092

"""


class UnsafeToDelete(Exception):
    pass


def raise_if_unsafe_to_delete(model):
    if model._meta.label == "popolo.Membership":
        if model.ballot.candidates_locked:
            raise UnsafeToDelete(
                "Can't delete a membership of a locked ballot ({})".format(
                    model.ballot.ballot_paper_id
                )
            )
    related_models = model_has_related_objects(model)
    if related_models:
        msg = (
            "Trying to delete a {model} (pk={pk}) that other "
            "objects depend on ({related_models})"
        )
        raise UnsafeToDelete(
            msg.format(
                model=model._meta.model.__name__,
                pk=model.id,
                related_models=str(related_models),
            )
        )


def model_has_related_objects(model):
    collector = NestedObjects(using="default")
    collector.collect([model])
    collected = collector.nested()
    if len(collected) >= 2:
        return collected[1]
    assert collected[0] == model
    return False


class BallotQueryset(models.QuerySet):
    def get_previous_ballot_for_post(self, ballot):
        """
        Given a ballot object, get the previous (by election date) ballot for
        the ballot's post.
        :type ballot: Ballot

        """

        qs = self.filter(
            post=ballot.post,
            election__election_date__lt=ballot.election.election_date,
        ).order_by("-election__election_date")

        if qs.exists():
            return qs.first()

        return None

    def get_next_ballot_for_post(self, ballot):
        """
        Given a ballot object, get the next (by election date) ballot for
        the ballot's post.
        :type ballot: Ballot

        """

        qs = self.filter(
            post=ballot.post,
            election__election_date__gt=ballot.election.election_date,
        ).order_by("election__election_date")

        if qs.exists():
            return qs.first()

        return None

    def current(self, current=True):
        return self.filter(election__current=current)

    def future(self):
        return self.filter(election__election_date__gt=timezone.now())

    def current_or_future(self):
        return self.filter(
            models.Q(election__current=True)
            | models.Q(election__election_date__gt=timezone.now())
        )


class Ballot(models.Model):
    post = models.ForeignKey("popolo.Post", on_delete=models.CASCADE)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    ballot_paper_id = models.CharField(blank=True, max_length=255, unique=True)

    candidates_locked = models.BooleanField(default=False)
    winner_count = models.PositiveSmallIntegerField(blank=True, null=True)
    cancelled = models.BooleanField(default=False)
    replaces = models.OneToOneField(
        "Ballot",
        null=True,
        blank=True,
        related_name="replaced_by",
        on_delete=models.DO_NOTHING,
    )

    tags = JSONField(default=dict)

    UnsafeToDelete = UnsafeToDelete

    objects = BallotQueryset.as_manager()

    def __str__(self):
        fmt = "<Ballot ballot_paper_id='{e}'{locked}{w}>"
        return fmt.format(
            e=self.ballot_paper_id,
            locked=(
                " candidates_locked=True" if self.candidates_locked else ""
            ),
            w=(
                " winner_count={}".format(self.winner_count)
                if (self.winner_count is not None)
                else ""
            ),
        )

    def get_absolute_url(self, viewname="election_view"):
        return reverse(viewname, args=[self.ballot_paper_id])

    def get_bulk_add_url(self):
        return self.get_absolute_url("bulk_add_from_sopn")

    def get_bulk_add_review_url(self):
        return self.get_absolute_url("bulk_add_sopn_review")

    def get_sopn_url(self):
        return self.get_absolute_url("ballot_paper_sopn")

    def safe_delete(self):
        collector = NestedObjects(using=connection.cursor().db.alias)
        collector.collect([self])
        if len(collector.nested()) > 1:
            raise self.UnsafeToDelete(
                "Can't delete PEE {} with related objects".format(
                    self.ballot_paper_id
                )
            )

        self.delete()

    @property
    def cancelled_status_text(self):
        if self.cancelled:
            return "(❌ cancelled)"

    @property
    def cancelled_status_html(self):
        if self.cancelled:
            return mark_safe(
                '<abbr title="The poll for this election was cancelled">{}</abbr>'.format(
                    self.cancelled_status_text
                )
            )
        return ""

    @property
    def locked_status_text(self):
        if self.candidates_locked:
            return mark_safe("🔐")

    @property
    def locked_status_html(self):
        if self.candidates_locked:
            return mark_safe(
                '<abbr title="Candidates verified and post locked">{}</abbr>'.format(
                    self.locked_status_text
                )
            )
        if self.has_lock_suggestion:
            self.suggested_lock_html
        return ""

    @property
    def suggested_lock_html(self):
        return mark_safe(
            '<abbr title="Someone suggested locking this post">🔓</abbr>'
        )

    @property
    def sopn(self):
        return self.officialdocument_set.filter(
            document_type=self.officialdocument_set.model.NOMINATION_PAPER
        ).latest()

    @cached_property
    def has_results(self):
        if getattr(self, "resultset", None):
            return True
        if self.membership_set.filter(elected=True).exists():
            return True
        return False

    @property
    def polls_closed(self):
        # TODO: City of London and other complex cases. Take this from EE?
        normal_poll_close_time = datetime.time(hour=22)

        poll_close_datetime = timezone.make_aware(
            datetime.datetime.combine(
                self.election.election_date, normal_poll_close_time
            )
        )
        return poll_close_datetime <= timezone.now()

    @property
    def has_lock_suggestion(self):
        return self.suggestedpostlock_set.exists()

    @property
    def get_winner_count(self):
        """
        Returns 0 rather than None if the winner_count is unknown. See comment in
        https://github.com/DemocracyClub/yournextrepresentative/pull/621#issuecomment-417252565

        :return:
        """
        if self.winner_count:
            return self.winner_count
        return 0

    @property
    def hashed_memberships(self):
        """
        Return an md5 hash based on the party, person and list position of the
        ballots candidates
        """
        membership_data = self.membership_set.values_list(
            "party", "person", "party_list_position"
        )
        membership_str = "".join(str(val) for val in membership_data)
        return hashlib.md5(membership_str.encode()).hexdigest()

    def delete_outdated_suggested_locks(self):
        """
        Deletes all SuggestedPostLock objects with outdated membership hash
        """
        return self.suggestedpostlock_set.exclude(
            ballot_hash=self.hashed_memberships
        ).delete()

    def user_can_edit_membership(self, user, allow_if_trusted_to_lock=True):
        """
        Can a given user edit this ballot?

        :type user: django.contrib.auth.models.User
        :type allow_if_trusted_to_lock: bool
        :param allow_if_trusted_to_lock:  If a user is trusted to lock then they
          can edit memberships. This is to support legacy behaviour that will be changed
          in future. See https://github.com/DemocracyClub/yournextrepresentative/issues/991
          for more
        """

        # users have to be logged in to an account
        if not user.is_authenticated:
            return False

        # If the ballot is unlocked and not cancelled, anyone
        # can edit the memberships
        if not self.candidates_locked and not self.cancelled:
            return True

        if (
            allow_if_trusted_to_lock
            and user.groups.filter(name=TRUSTED_TO_LOCK_GROUP_NAME).exists()
        ):
            return True

        # Special case where elections are cancelled before they are locked
        # Don't allow most people to edit them, but do allow staff to
        if self.cancelled and not self.candidates_locked and user.is_staff:
            return True

        return False

    def people_not_standing_again(self, previous_ballot):
        """
        Returns a queryset of People objects that are known not to be standing
        again for this ballot.

        "Not standing again" means that the person stood in this ballot's post
        previously and someone has asserted that they're not standing again.

        The current data model only stores "not standing" against an election,
        not a post or ballot, so we have to filter all people not standing
        in this election by the post they previously stood in.

        """

        return self.election.persons_not_standing_tmp.filter(
            memberships__ballot=previous_ballot
        ).only("pk")


class PartySet(models.Model):
    slug = models.CharField(max_length=256, unique=True)
    name = models.CharField(max_length=1024)
    parties = models.ManyToManyField(
        "popolo.Organization", related_name="party_sets"
    )

    def __str__(self):
        return self.name
