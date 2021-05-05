from random import randrange

from django.utils.html import escape
from django_webtest import WebTest
from sorl.thumbnail import get_thumbnail

from candidates.models import PartySet
from candidates.models.popolo_extra import Ballot
from candidates.tests.auth import TestUserMixin
from candidates.tests.dates import date_in_near_future, date_in_near_past
from candidates.tests.factories import (
    BallotPaperFactory,
    ElectionFactory,
    MembershipFactory,
    OrganizationFactory,
    PostFactory,
)
from elections.filters import (
    BaseBallotFilter,
    CurrentOrFutureBallotFilter,
    region_choices,
)
from utils.dict_io import BufferDictReader
from elections.tests.data_timeline_helper import DataTimelineHTMLAssertions
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME
from parties.tests.factories import PartyFactory
from people.models import Person, PersonImage
from people.tests.factories import PersonFactory
from popolo.models import Membership
from uk_results.models import CandidateResult, ResultSet
from utils.testing_utils import FuzzyInt


class SingleBallotStatesMixin:
    def create_election(self, election_name, date=None):
        kwargs = {"name": election_name}
        if date:
            kwargs["election_date"] = date
        else:
            kwargs["election_date"] = date_in_near_future

        return ElectionFactory(**kwargs)

    def create_post(self, post_label):
        ps, _ = PartySet.objects.update_or_create(slug="GB")
        org = OrganizationFactory(name="Baz council")
        return PostFactory(label=post_label, organization=org, party_set=ps)

    def create_ballot(
        self, ballot_paper_id, election, post, winner_count=1, **kwargs
    ):
        return BallotPaperFactory(
            ballot_paper_id=ballot_paper_id,
            election=election,
            post=post,
            winner_count=winner_count,
            **kwargs,
        )

    def create_party(self):
        return PartyFactory()

    def create_parties(self, number):
        return [self.create_party() for i in range(number)]

    def create_memberships(self, ballot, parties):
        for i in range(3):
            for party in parties:
                person = PersonFactory()
                MembershipFactory(ballot=ballot, person=person, party=party)


class TestBallotView(
    TestUserMixin, SingleBallotStatesMixin, DataTimelineHTMLAssertions, WebTest
):
    def setUp(self):
        super().setUp()
        self.election = self.create_election("Foo Local Election")
        self.post = self.create_post("Bar Ward")
        self.ballot = self.create_ballot(
            "local.foo.bar.2019-08-03", self.election, self.post, winner_count=2
        )

        self.past_election = self.create_election(
            "Foo Local election", date=date_in_near_past
        )
        self.past_ballot = self.create_ballot(
            "local.foo.bar.{}".format(date_in_near_past.isoformat()),
            self.past_election,
            self.post,
            winner_count=2,
        )

        self.parties = self.create_parties(3)

    def test_ballot_just_created(self):
        """
        New ballot, just imported from EE, no data against it yet
        """
        with self.assertNumQueries(FuzzyInt(7, 10)):
            response = self.app.get(self.ballot.get_absolute_url())

        self.assertContains(
            response,
            "We don’t know of any candidates in Bar Ward for the Foo Local Election yet.",
        )

        self.assertDataTimelineCandidateAddingInProgress(response)

    def test_ballot_sopn_upload_link(self):
        self.create_memberships(self.ballot, self.parties)
        response = self.app.get(
            self.ballot.get_absolute_url(),
            user=self.user_who_can_upload_documents,
        )
        self.assertContains(
            response,
            '<a href="/upload_document/{}/" class="button">Upload SOPN</a>'.format(
                self.ballot.ballot_paper_id
            ),
        )

    def test_ballot_with_candidates_no_sopn(self):

        self.create_memberships(self.ballot, self.parties)
        response = self.app.get(self.ballot.get_absolute_url())

        self.assertEqual(response.context["candidates"].count(), 9)
        self.assertDataTimelineCandidateAddingInProgress(response)
        self.assertInHTML("<h1>Candidates for Bar Ward</h1>", response.text)
        self.assertInHTML(
            """
            <p>
                These candidates haven't been confirmed by the official
                "nomination papers" from the council yet. This means they might
                not all end up on the ballot paper.
            </p>
            """,
            response.text,
        )
        self.assertInHTML(
            """
            <thead>
              <tr>
                <th>Name</th>
                <th>Party</th>
              </tr>
            </thead>
        """,
            response.text,
        )

    def test_all_expected_people_in_table(self):
        self.create_memberships(self.ballot, self.parties)
        response = self.app.get(self.ballot.get_absolute_url())
        for membership in self.ballot.membership_set.all():
            self.assertContains(response, escape(membership.person.name))
            self.assertContains(response, membership.party.name)

    def test_person_photo_shown(self):
        self.create_memberships(self.ballot, self.parties)
        person = self.ballot.membership_set.first().person
        im = PersonImage.objects.update_or_create_from_file(
            EXAMPLE_IMAGE_FILENAME,
            "images/imported.jpg",
            person=person,
            defaults={
                "md5sum": "md5sum",
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "Here's an image...",
                "is_primary": True,
                "source": "Found on the candidate's Flickr feed",
            },
        )
        expected_url = get_thumbnail(im.image, "x64").url
        response = self.app.get(self.ballot.get_absolute_url())
        response.mustcontain(expected_url)

    def test_any_constituency_csv(self):
        self.create_memberships(self.ballot, self.parties)
        url = "{}.csv".format(self.ballot.get_absolute_url().rstrip("/"))
        response = self.app.get(url)
        self.assertEqual(response.status_code, 200)
        row_dicts = [row for row in BufferDictReader(response.content)]
        self.assertEqual(9, len(row_dicts))
        membership = self.ballot.membership_set.order_by("person__pk").first()
        self.maxDiff = None
        self.assertDictEqual(
            dict(row_dicts[0]),
            {
                "ballot_paper_id": "local.foo.bar.2019-08-03",
                "blog_url": "",
                "birth_date": "",
                "cancelled_poll": "False",
                "elected": "",
                "election": self.ballot.election.slug,
                "election_current": "True",
                "election_date": self.ballot.election.election_date.isoformat(),
                "email": "",
                "facebook_page_url": "",
                "facebook_personal_url": "",
                "favourite_biscuits": "",
                "gender": "",
                "gss_code": "",
                "homepage_url": "",
                "honorific_prefix": "",
                "honorific_suffix": "",
                "id": str(membership.person.pk),
                "image_copyright": "",
                "image_uploading_user": "",
                "image_uploading_user_notes": "",
                "image_url": "",
                "instagram_url": "",
                "linkedin_url": "",
                "name": membership.person.name,
                "NUTS1": "",
                "old_person_ids": "",
                "organisation_name": "Baz council",
                "parlparse_id": "",
                "party_ec_id": membership.party.ec_id,
                "party_id": membership.party.legacy_slug,
                "party_lists_in_use": "False",
                "party_list_position": "",
                "party_name": membership.party_name,
                "party_description_text": "",
                "party_ppc_page_url": "",
                "post_id": self.ballot.post.slug,
                "post_label": self.ballot.post.label,
                "proxy_image_url_template": "",
                "seats_contested": "2",
                "theyworkforyou_url": "",
                "twitter_username": "",
                "twitter_user_id": "",
                "wikipedia_url": "",
                "wikidata_id": "",
                "youtube_profile": "",
            },
        )

    def test_ballot_with_winner(self):
        self.create_memberships(self.past_ballot, self.parties)
        response = self.app.get(self.past_ballot.get_absolute_url())
        self.assertDataTimelineNoResults(response)

        rs = ResultSet.objects.create(ballot=self.past_ballot)
        for i, membership in enumerate(self.past_ballot.membership_set.all()):
            if i in range(0, self.past_ballot.winner_count):
                winner = True
            else:
                winner = False
            CandidateResult.objects.create(
                result_set=rs,
                membership=membership,
                num_ballots=randrange(1, 1000),
                is_winner=winner,
            )

        response = self.app.get(self.past_ballot.get_absolute_url())
        response.mustcontain("Winner(s) recorded")
        response.mustcontain(no="Winner(s) unknown")
        response.mustcontain(no="Waiting for election to happen")
        response.mustcontain(no="Unset the current winners")
        # TODO: Test winners in table

    def test_constituency_with_winner_record_results_user(self):
        self.ballot.election.election_date = "2015-05-07"
        self.ballot.election.save()
        self.create_memberships(self.ballot, self.parties)
        self.ballot.membership_set.update(elected=True)
        response = self.app.get(
            self.ballot.get_absolute_url(),
            user=self.user_who_can_record_results,
        )
        response.mustcontain("Unset the current winners")

    def test_constituency_with_may_be_standing(self):
        self.create_memberships(self.past_ballot, self.parties)
        response = self.app.get(self.ballot.get_absolute_url(), user=self.user)
        response.mustcontain(
            "Is a candidate from an earlier election standing again?"
        )

    def test_constituency_with_not_standing(self):
        self.create_memberships(self.past_ballot, self.parties)
        person_not_standing = Person.objects.filter(
            memberships__ballot=self.past_ballot
        ).first()
        person_not_standing.not_standing.add(self.ballot.election)
        response = self.app.get(self.ballot.get_absolute_url(), user=self.user)
        response.mustcontain(
            "These people from earlier elections are known not to be standing again"
        )

    def test_mark_not_standing_no_candidate(self):
        self.create_memberships(self.past_ballot, self.parties)
        person_to_mark = Person.objects.filter(
            memberships__ballot=self.past_ballot
        ).first()
        response = self.app.get(self.ballot.get_absolute_url(), user=self.user)

        form = response.forms["candidacy-delete_{}".format(person_to_mark.pk)]
        form["person_id"] = 9999
        form["source"] = "test data"
        response = form.submit(expect_errors=True)
        self.assertEqual(response.status_code, 404)

    def test_mark_standing_no_candidate(self):
        self.create_memberships(self.past_ballot, self.parties)
        person_to_mark = Person.objects.filter(
            memberships__ballot=self.past_ballot
        ).first()
        response = self.app.get(self.ballot.get_absolute_url(), user=self.user)

        form = response.forms["candidacy-create_{}".format(person_to_mark.pk)]
        form["person_id"] = 00000
        form["source"] = "test data"

        response = form.submit(expect_errors=True)
        self.assertEqual(response.status_code, 404)

    def test_mark_candidate_not_standing(self):
        self.create_memberships(self.past_ballot, self.parties)
        person_to_mark = Person.objects.filter(
            memberships__ballot=self.past_ballot
        ).first()
        response = self.app.get(self.ballot.get_absolute_url(), user=self.user)

        form = response.forms["candidacy-delete_{}".format(person_to_mark.pk)]
        form["person_id"] = person_to_mark.pk
        form["source"] = "test data"
        response = form.submit()
        self.assertEqual(response.status_code, 302)

        self.assertFalse(self.ballot.membership_set.exists())
        self.assertTrue(
            self.ballot.election in person_to_mark.not_standing.all()
        )

    def test_mark_may_stand_actually_standing(self):
        self.assertFalse(self.ballot.membership_set.exists())
        self.create_memberships(self.past_ballot, self.parties)

        person_to_mark = Person.objects.filter(
            memberships__ballot=self.past_ballot
        ).first()
        response = self.app.get(self.ballot.get_absolute_url(), user=self.user)

        form = response.forms["candidacy-create_{}".format(person_to_mark.pk)]
        form["person_id"] = person_to_mark.pk
        form["source"] = "test data"
        response = form.submit()
        self.assertEqual(response.status_code, 302)

        membership = Membership.objects.filter(
            person=person_to_mark, ballot=self.ballot
        )

        self.assertTrue(membership.exists())

    def test_mark_may_stand_not_standing_again(self):
        self.create_memberships(self.past_ballot, self.parties)

        person_to_mark = Person.objects.filter(
            memberships__ballot=self.past_ballot
        ).first()
        response = self.app.get(self.ballot.get_absolute_url(), user=self.user)

        form = response.forms["candidacy-delete_{}".format(person_to_mark.pk)]
        form["person_id"] = person_to_mark.pk
        form["source"] = "test data"
        response = form.submit()
        self.assertEqual(response.status_code, 302)

        membership = Membership.objects.filter(
            person=person_to_mark, ballot=self.ballot
        )
        self.assertFalse(membership.exists())

        not_standing = person_to_mark.not_standing.all()
        self.assertTrue(self.ballot.election in not_standing)

    def test_mark_not_standing_standing_again(self):
        self.create_memberships(self.past_ballot, self.parties)

        person_to_mark = Person.objects.filter(
            memberships__ballot=self.past_ballot
        ).first()
        person_to_mark.not_standing.add(self.ballot.election)

        membership = Membership.objects.filter(
            person=person_to_mark, ballot=self.ballot
        )
        self.assertFalse(membership.exists())

        response = self.app.get(self.ballot.get_absolute_url(), user=self.user)

        form = response.forms["candidacy-create_{}".format(person_to_mark.pk)]
        form["person_id"] = person_to_mark.pk
        form["source"] = "test data"
        response = form.submit()
        self.assertEqual(response.status_code, 302)

        membership = Membership.objects.filter(
            person=person_to_mark, ballot=self.ballot
        )
        self.assertTrue(membership.exists())

        not_standing = person_to_mark.not_standing.all()
        self.assertFalse(self.election in not_standing)

    def test_constituency_with_no_winner_record_results_user(self):
        response = self.app.get(
            self.ballot.get_absolute_url(),
            user=self.user_who_can_record_results,
        )
        response.mustcontain(no="Unset the current winners")


class TestBallotFilter(SingleBallotStatesMixin, WebTest):
    def setUp(self):
        self.election = self.create_election("Foo Election")
        self.post = self.create_post("Bar")

    def test_region_choices(self):
        assert region_choices() == [
            ("UKC", "North East"),
            ("UKD", "North West"),
            ("UKE", "Yorkshire and the Humber"),
            ("UKF", "East Midlands"),
            ("UKG", "West Midlands"),
            ("UKH", "East of England"),
            ("UKI", "London"),
            ("UKJ", "South East"),
            ("UKK", "South West"),
            ("UKL", "Wales"),
            ("UKM", "Scotland"),
            ("UKN", "Northern Ireland"),
        ]

    def test_region_filter(self):
        """
        Create a single ballot with a nuts1 tag for each region.
        Then filter by each region and assert the expected ballot is returned.
        """
        for region in region_choices():
            self.create_ballot(
                f"local.{region[0]}.2021-05-06",
                self.election,
                self.post,
                tags={"NUTS1": {"key": region[0], "value": region[1]}},
            )
        queryset = Ballot.objects.all()
        self.assertEqual(queryset.count(), 12)
        ballot_filter = BaseBallotFilter()
        for region in region_choices():
            with self.subTest(msg=region[0]):
                results = ballot_filter.region_filter(
                    queryset=queryset, name=region[1], value=region[0]
                )
                expected = Ballot.objects.get(
                    ballot_paper_id=f"local.{region[0]}.2021-05-06"
                )
                self.assertIn(expected, results)
                self.assertEqual(results.count(), 1)

    def test_has_results(self):
        ballot_with_results = self.create_ballot(
            ballot_paper_id="local.has-results.2021-05-06",
            election=self.election,
            post=self.post,
        )
        ResultSet.objects.create(
            ballot=ballot_with_results,
            num_turnout_reported=10000,
            num_spoilt_ballots=30,
            source="Example ResultSet for testing",
        )
        ballot_without_results = self.create_ballot(
            ballot_paper_id="local.no-results.2021-05-06",
            election=self.election,
            post=self.post,
        )

        filter = CurrentOrFutureBallotFilter()
        ballots = Ballot.objects.all()
        for case in [True, False]:
            with self.subTest(msg=case):
                results = filter.has_results_filter(
                    queryset=ballots, name=case, value=case
                )
                self.assertEqual(ballot_with_results in results, case)
                self.assertEqual(ballot_without_results in results, not case)
