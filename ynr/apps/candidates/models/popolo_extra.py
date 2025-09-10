import datetime
import hashlib

from candidates.helpers.helpers import get_election_timetable
from candidates.models import LoggedAction
from candidates.models.auth import TRUSTED_TO_LOCK_GROUP_NAME
from candidates.models.db import ActionType
from django.conf import settings
from django.contrib.admin.utils import NestedObjects
from django.db import connection, models
from django.db.models import Count, Exists, F, JSONField, Max, OuterRef
from django.db.models.functions import Greatest
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.html import mark_safe, urlize
from django.utils.http import urlencode
from elections.models import Election
from moderation_queue.models import QueuedImage
from popolo.models import Membership
from uk_election_ids.datapackage import VOTING_SYSTEMS
from utils.mixins import EEModifiedMixin

"""Extensions to the base django-popolo classes for YourNextRepresentative

These are done via explicit one-to-one fields to avoid the performance
problems with multi-table inheritance; it's preferable to state when you
want a join or not.

  http://stackoverflow.com/q/23466577/223092

"""


class UnsafeToDelete(Exception):
    pass


def raise_if_unsafe_to_delete(model):
    if (
        model._meta.label == "popolo.Membership"
        and model.ballot.candidates_locked
    ):
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


class ByElectionReason(models.TextChoices):
    """
    Reasons why a by-election may be triggered.

    Not all of these can be applied to all election types.

    e.g. a recall petition is only used in Westminster, and failure to attend meetings
    applies to local government.

    An empty string represents ballots that are not applicable, e.g because they're not by-elections.

    The choices here are in part based on:
        UK Electoral Commission guidance on casual vacancies:
        https://www.electoralcommission.org.uk/guidance-returning-officers-administering-local-government-elections-england/casual-vacancies-and-elections/how-casual-vacancies-occur
    """

    DEATH = "DEATH", "The elected member died"
    RESIGNATION = "RESIGNATION", "The elected member resigned"
    ELECTORAL_COURT = (
        "ELECTORAL_COURT",
        "The election of the elected member was declared void by an election court",
    )
    FAILURE_TO_ACCEPT = (
        "FAILURE_TO_ACCEPT",
        "The previous election winner did not sign a declaration of acceptance",
    )
    FAILURE_TO_ATTEND_MEETINGS = (
        "FAILURE_TO_ATTEND_MEETINGS",
        "The elected member failed to attend meetings for six months",
    )
    DISQUALIFICATION = "DISQUALIFICATION", "The elected member was disqualified"
    LOSING_QUALIFICATION = (
        "LOSING_QUALIFICATION",
        "The elected member no longer qualified as a registered elector",
    )
    RECALL_PETITION = (
        "RECALL_PETITION",
        "The elected member was recalled by a successful recall petition",
    )
    OTHER = "OTHER", "Other"
    UNKNOWN = "UNKNOWN", "Unknown"
    NOT_APPLICABLE = "", "Neither a by-election nor a ballot"


class BallotQueryset(models.QuerySet):
    _current = False

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
        self._current = True
        return self.filter(election__current=current)

    def future(self):
        return self.filter(election__election_date__gt=timezone.now())

    def current_or_future(self):
        self._current = True
        return self.filter(
            models.Q(election__current=True)
            | models.Q(election__election_date__gt=timezone.now())
        )

    def by_region(self, code):
        """
        Filter by NUTS1 code stored in the objects tags.
        """
        return self.filter(tags__NUTS1__key=code)

    def by_nation(self, *nation_codes):
        """
        Filter by nation
        """
        nuts_codes = []
        for nation_code in nation_codes:
            assert (
                nation_code in settings.NUTS_TO_NATION
            ), f"Unknown nation {nation_code}"
            nuts_codes += settings.NUTS_TO_NATION[nation_code]

        return self.filter(tags__NUTS1__key__in=nuts_codes)

    def for_postcode(self, postcode):
        kwargs = {"ids_only": True, "current_only": False}
        if self._current:
            kwargs["current_only"] = True
        from elections.uk.geo_helpers import get_ballots_from_postcode

        ballots = get_ballots_from_postcode(postcode, **kwargs)
        return self.filter(ballot_paper_id__in=ballots)

    def has_results(self):
        """
        Return a QuerySet of ballots that have a membership with candidate results
        """
        return self.annotate(
            has_winner=Exists(
                Membership.objects.filter(ballot=OuterRef("pk"), elected=True)
            )
        ).filter(has_winner=True)

    def no_results(self):
        """
        Return a QuerySet of ballots that excluding those with a candidate marked elected
        """
        return self.filter(models.Q(membership__elected=False))

    def incomplete_result_set(self):
        """
        Return a QuerySet of ballots that some combination
        of ballot results that are missing.
        """
        return self.filter(
            models.Q(
                resultset__num_turnout_reported__isnull=True,
                resultset__num_spoilt_ballots__isnull=False,
                resultset__total_electorate__isnull=False,
            )
            | models.Q(
                resultset__num_turnout_reported__isnull=False,
                resultset__num_spoilt_ballots__isnull=True,
                resultset__total_electorate__isnull=False,
            )
            | models.Q(
                resultset__num_turnout_reported__isnull=False,
                resultset__num_spoilt_ballots__isnull=False,
                resultset__total_electorate__isnull=True,
            )
        ).distinct()

    def complete_result_set(self):
        """
        Return a QuerySet of ballots that have a complete result set
        """
        return self.filter(
            resultset__num_turnout_reported__isnull=False,
            resultset__num_spoilt_ballots__isnull=False,
            resultset__total_electorate__isnull=False,
        ).distinct()

    def no_result_set(self):
        """
        Return a QuerySet of ballots that have no result set
        """
        return self.filter(resultset__isnull=True).distinct()

    def with_last_updated(self):
        """
        Annotates the last_updated field to objects, which represents the most
        recent modified timstamp out of the ballot, related election, post or
        the most recently updated related candidate
        """
        return (
            self.annotate(
                membership_modified_max=Max("membership__modified"),
                last_updated=Greatest(
                    "modified",
                    "election__modified",
                    "post__modified",
                    "membership_modified_max",
                ),
            )
            .distinct()
            .order_by("last_updated")
        )

    def last_updated(self, datetime):
        """
        Filter on the last_updated timestamp
        """
        return self.with_last_updated().filter(last_updated__gt=datetime)

    def ordered_by_latest_ee_modified(self):
        """
        Takes the most recent ee_modified value between the Ballot and the
        Election and orders the queryset by it, most recent first.
        The 'Greatest' function is used to determine which value is more recent
        between the datetime on the Ballot or the Election.
        This is because in EveryElection a Ballot and Election are both Election
        objects. So when we order elections by their ee_modified date, we have
        to look across both models in YNR to get the most recent timestamp.
        """
        return (
            self.annotate(
                latest_ee_modified=Greatest(
                    "ee_modified", "election__ee_modified"
                )
            )
            .filter(latest_ee_modified__isnull=False)
            .order_by("-latest_ee_modified")
        )

    def uncontested(self):
        """
        Return a QuerySet of ballots that are uncontested
        """
        return (
            self.annotate(memberships_count=Count("membership"))
            .filter(winner_count__gte=F("memberships_count"))
            .filter(candidates_locked=True)
        )


class Ballot(EEModifiedMixin, models.Model):
    VOTING_SYSTEM_FPTP = "FPTP"

    post = models.ForeignKey("popolo.Post", on_delete=models.CASCADE)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    ballot_paper_id = models.CharField(blank=True, max_length=255, unique=True)

    candidates_locked = models.BooleanField(default=False)
    winner_count = models.PositiveSmallIntegerField(
        blank=True, null=False, default=1
    )
    cancelled = models.BooleanField(default=False)
    replaces = models.OneToOneField(
        "Ballot",
        null=True,
        blank=True,
        related_name="replaced_by",
        on_delete=models.DO_NOTHING,
    )
    voting_system = models.CharField(
        blank=True,
        max_length=255,
        choices=[(key, value["name"]) for key, value in VOTING_SYSTEMS.items()],
    )

    tags = JSONField(default=dict, blank=True)

    by_election_reason = models.CharField(
        max_length=30,
        null=False,
        blank=True,
        choices=ByElectionReason.choices,
        default=ByElectionReason.NOT_APPLICABLE,
        help_text=urlize(ByElectionReason.__doc__),
    )

    UnsafeToDelete = UnsafeToDelete

    objects = BallotQueryset.as_manager()

    def __str__(self):
        fmt = "<Ballot ballot_paper_id='{e}'{locked}{w}>"
        return fmt.format(
            e=self.ballot_paper_id,
            locked=(
                " candidates_locked=True" if self.candidates_locked else ""
            ),
            w=(" winner_count={}".format(self.winner_count)),
        )

    def get_absolute_url(self, viewname="election_view"):
        return reverse(viewname, args=[self.ballot_paper_id])

    def get_bulk_add_url(self):
        return self.get_absolute_url("bulk_add_from_sopn")

    def get_bulk_add_review_url(self):
        return self.get_absolute_url("bulk_add_sopn_review")

    def get_sopn_url(self):
        return self.get_absolute_url("ballot_paper_sopn")

    def get_results_url(self):
        """
        Get url to direct user to enter results. Currently only FPTP
        supports full results, otherwise we direct user to the ballot
        view where they can mark individual candidates as elected.
        """
        if self.can_enter_votes_cast:
            return self.get_absolute_url(viewname="ballot_paper_results_form")
        return self.get_absolute_url()

    def num_candidates(self):
        return self.membership_set.count()

    @property
    def results_button_text(self):
        """
        Allows different button text depending on the voting system
        """
        mapping = {self.VOTING_SYSTEM_FPTP: "Add results"}
        return mapping.get(self.voting_system, "Mark elected candidates")

    @property
    def can_enter_votes_cast(self):
        """
        Return boolean for if this ballot uses First Past The Post
        """
        return self.voting_system in [self.VOTING_SYSTEM_FPTP]

    @property
    def nice_voting_system(self):
        voting_systems = {
            "STV": "Single Transferable Vote",
            "FPTP": "First Past The Post",
            "SV": "Supplementary Vote",
            "AMS": "Additional Member System",
        }
        voting_system_slug = self.voting_system.upper()
        return voting_systems.get(voting_system_slug, voting_system_slug)

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
        return None

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
        return None

    @property
    def locked_status_html(self):
        if self.candidates_locked:
            return mark_safe(
                '<abbr title="Candidates verified and post locked">{}</abbr>'.format(
                    self.locked_status_text
                )
            )
        if self.has_lock_suggestion:
            return self.suggested_lock_html
        return ""

    @property
    def suggested_lock_html(self):
        return mark_safe(
            '<abbr title="Someone suggested locking this post">🔓</abbr>'
        )

    @cached_property
    def has_results(self):
        """Return a boolean if the ballot has candidate results"""
        if self.membership_set.filter(elected=True).exists():
            return True
        return False

    @property
    def uncontested(self):
        if not self.candidates_locked:
            return False
        if self.winner_count >= self.membership_set.count():
            return True
        return False

    @property
    def looks_uncontested(self):
        """
        Does the ballot have more or equal seats up than candidates
        """
        return self.winner_count >= self.membership_set.count()

    def mark_uncontested_winners(self, ip_address=None, user=None):
        """
        If the election is uncontested mark all candidates as elected
        """
        if not self.uncontested:
            return
        self.membership_set.update(elected=True)
        winners = self.membership_set.filter(elected=True)
        for winner in winners:
            LoggedAction.objects.create(
                action_type=ActionType.SET_CANDIDATE_ELECTED,
                ip_address=ip_address,
                user=user,
                ballot=self,
                person=winner.person,
                source="Ballot was uncontested",
            )

    def unmark_uncontested_winners(self, ip_address=None, user=None):
        """
        Do nothing if we dont have any elected candidates
        Do nothing if we have results, but they were not marked
        winners because ballot looks uncontested
        Otherwise unmark winners and create logged actions
        """
        if not self.has_results:
            return

        if not self.looks_uncontested:
            return

        self.membership_set.update(elected=None)
        candidates_not_elected = self.membership_set.filter(elected=None)
        for candidate in candidates_not_elected:
            LoggedAction.objects.create(
                action_type=ActionType.SET_CANDIDATE_NOT_ELECTED,
                ip_address=ip_address,
                user=user,
                ballot=self,
                person=candidate.person,
                source="Ballot was previously marked uncontested, but may now have been unlocked. Check the ballot for more details.",
            )

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
    def results_completed(self):
        """
        Return a boolean if the result_set is complete for this ballot
        """
        return self.filter(
            models.Q(resultset__isnull=False)
            | models.Q(membership__elected=True)
            | models.Q(membership__turnout__isnull=False)
            | models.Q(membership__spoilt_ballots__isnull=False)
            | models.Q(membership__num_ballots__isnull=False)
        ).distinct()

    @property
    def has_lock_suggestion(self):
        return self.suggestedpostlock_set.exists()

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

        if (
            allow_if_trusted_to_lock
            and user.groups.filter(name=TRUSTED_TO_LOCK_GROUP_NAME).exists()
            and not self.candidates_locked
        ):
            return True

        # If the ballot is unlocked and not cancelled, anyone
        # can edit the memberships. Also prevent adding via the ballot
        # forms when we have a SOPN for this ballot, as the bulk adding forms
        # should be used instead.
        if (
            not self.candidates_locked
            and not self.cancelled
            and not hasattr(self, "sopn")
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

    @cached_property
    def get_absolute_queued_image_review_url(self):
        """
        If the ballot has candidates with undecided images, returns a URL to the
        moderation queue list review page, filtered by this ballot paper ID
        """
        if not self.membership_set.filter(
            person__queuedimage__decision=QueuedImage.UNDECIDED
        ).exists():
            return ""

        querystring = urlencode({"ballot_paper_id": self.ballot_paper_id})
        url = reverse("photo-review-list")
        return f"{url}?{querystring}"

    @property
    def is_welsh_run(self):
        """
        Return a boolean if this is a Welsh government run ballot
        """
        if self.ballot_paper_id.startswith("senedd."):
            return True

        if not self.ballot_paper_id.startswith("local."):
            return False

        return self.tags.get("NUTS1", {}).get("key") == "UKL"

    @property
    def expected_sopn_date(self):
        try:
            return get_election_timetable(
                self.ballot_paper_id, self.post.territory_code
            ).sopn_publish_date

        except AttributeError:
            return None


class PartySet(models.Model):
    slug = models.CharField(max_length=256, unique=True)
    name = models.CharField(max_length=1024)
    parties = models.ManyToManyField(
        "popolo.Organization", related_name="party_sets"
    )

    def __str__(self):
        return self.name
