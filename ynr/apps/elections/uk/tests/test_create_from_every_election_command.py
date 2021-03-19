from urllib.parse import urljoin

from django.conf import settings
from django.core.management import call_command
from django_webtest import WebTest
from freezegun import freeze_time
from mock import Mock, patch

from candidates.models import Ballot
from candidates.tests.factories import (
    MembershipFactory,
    PostFactory,
    ElectionFactory,
    OrganizationFactory,
)
from elections.uk import every_election
from people.tests.factories import PersonFactory
from popolo.models import Post

from .ee_import_results import (
    current_elections,
    current_elections_page_2,
    duplicate_post_names,
    each_type_of_election_on_one_day,
    local_highland,
    no_results,
    pre_gss_result,
    post_gss_result,
    replaced_election,
    duplicate_post_and_election,
)

EE_BASE_URL = getattr(
    settings, "EE_BASE_URL", "https://elections.democracyclub.org.uk/"
)


def create_mock_with_fixtures(fixtures):
    def mock(url):
        try:
            return Mock(
                **{"json.return_value": fixtures[url], "status_code": 200}
            )
        except KeyError:
            raise Exception("URL that hasn't been mocked yet: " + url)

    return mock


fake_requests_current_elections = create_mock_with_fixtures(
    {
        urljoin(
            EE_BASE_URL, "/api/elections/?poll_open_date__gte=2018-01-03"
        ): current_elections,
        urljoin(
            EE_BASE_URL,
            "/api/elections/?poll_open_date__gte=fakedate&limit=100&offset=100",
        ): current_elections_page_2,
        urljoin(
            EE_BASE_URL,
            "/api/elections/?current=True&poll_open_date=2019-01-17",
        ): each_type_of_election_on_one_day,
    }
)

fake_requests_each_type_of_election_on_one_day = create_mock_with_fixtures(
    {
        urljoin(
            EE_BASE_URL, "/api/elections/?poll_open_date__gte=2018-01-03"
        ): each_type_of_election_on_one_day,
        urljoin(
            EE_BASE_URL,
            "/api/elections/?deleted=1&poll_open_date__gte=2018-01-03",
        ): no_results,
    }
)


class EE_ImporterTest(WebTest):
    @patch("elections.uk.every_election.requests")
    @freeze_time("2018-02-02")
    def setUp(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_current_elections

        self.ee_importer = every_election.EveryElectionImporter()
        self.ee_importer.build_election_tree()

        self.parent_id = "local.brent.2018-02-22"  # they're good elections
        self.child_id = "local.brent.alperton.2018-02-22"

    def tearDown(self):
        every_election.POST_CACHE = {}
        every_election.ELECTION_CACHE = {}
        every_election.PARTYSET_CACHE = {}

    def test_ee_importer_build_tree(self):
        self.assertEqual(len(self.ee_importer.election_tree.keys()), 200)
        self.assertEqual(len(self.ee_importer.ballot_ids.keys()), 189)

        self.assertEqual(
            type(self.ee_importer.election_tree[self.parent_id]),
            every_election.EEElection,
        )

    def test_ee_importer_parent_from_string(self):
        parent = self.ee_importer.get_parent(self.child_id)
        self.assertEqual(parent["election_id"], self.parent_id)

    def test_create_election_from_election_dict(self):
        election = self.ee_importer.election_tree[self.parent_id]

        # Start with no elections
        self.assertEqual(every_election.YNRElection.objects.all().count(), 0)

        # Create and election from the API dict and verify it's there
        election.get_or_create_election()
        self.assertEqual(every_election.YNRElection.objects.all().count(), 1)
        self.assertTrue(election.election_created)

        # Create the same election again and check it's not duplicated
        with self.assertNumQueries(0):
            election.get_or_create_election()
            self.assertFalse(election.election_created)
        self.assertEqual(every_election.YNRElection.objects.all().count(), 1)

        # Check other info about the election
        self.assertEqual(election.election_object.name, "Brent local election")

        self.assertEqual(election.election_object.party_lists_in_use, False)
        self.assertEqual(
            election.organization_object.name, "London Borough of Brent"
        )
        self.assertTrue(election.organization_created)

    def test_create_organization_from_election_dict(self):
        election = self.ee_importer.election_tree[self.parent_id]

        # Create and election from the API dict and verify it's there
        election.get_or_create_organisation()
        self.assertTrue(election.organization_created)

        # Check other info about the election
        self.assertEqual(
            election.organization_object.name, "London Borough of Brent"
        )
        self.assertEqual(
            election.organization_object.slug, "local-authority:brent"
        )
        with self.assertNumQueries(0):
            election.get_or_create_organisation()
        self.assertFalse(election.organization_created)

    def test_create_post_from_election_group_dict(self):
        # We can't make a post from an "election"
        election = self.ee_importer.election_tree[self.parent_id]
        with self.assertRaises(ValueError):
            election.get_or_create_post()

    def test_create_post_from_ballot_id_dict(self):
        self.assertEqual(every_election.Post.objects.all().count(), 0)
        election = self.ee_importer.election_tree[self.child_id]
        election.get_or_create_post()
        self.assertTrue(election.post_created)
        election.get_or_create_post()
        self.assertFalse(election.post_created)
        self.assertEqual(every_election.Post.objects.all().count(), 1)

        self.assertEqual(election.party_set_object.name, "Great Britain")
        self.assertEqual(election.post_object.label, "Alperton")

    def test_create_post__election_from_ballot_id_dict(self):
        self.assertEqual(every_election.Post.objects.all().count(), 0)
        self.assertEqual(every_election.YNRElection.objects.all().count(), 0)
        election = self.ee_importer.election_tree[self.child_id]

        parent = self.ee_importer.get_parent(self.child_id)
        election.get_or_create_ballot(parent=parent)

        self.assertTrue(election.post_created)
        with self.assertNumQueries(0):
            election.get_or_create_ballot(parent=parent)
            election.get_or_create_post()
        self.assertFalse(election.post_created)

        self.assertEqual(every_election.Post.objects.all().count(), 1)

        self.assertEqual(election.party_set_object.name, "Great Britain")
        self.assertEqual(election.post_object.label, "Alperton")

    def test_create_many_elections_and_posts(self):
        for ballot_id, election_dict in self.ee_importer.ballot_ids.items():
            parent = self.ee_importer.get_parent(ballot_id)
            election_dict.get_or_create_ballot(parent=parent)
        self.assertEqual(every_election.Post.objects.all().count(), 189)
        self.assertEqual(every_election.YNRElection.objects.all().count(), 10)

    @patch("elections.uk.every_election.requests")
    def test_create_from_all_elections(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_current_elections
        query_args = {"poll_open_date": "2019-01-17", "current": "True"}
        self.ee_importer = every_election.EveryElectionImporter(query_args)
        self.ee_importer.build_election_tree()

        for ballot_id, election_dict in self.ee_importer.ballot_ids.items():
            parent = self.ee_importer.get_parent(ballot_id)
            election_dict.get_or_create_ballot(parent=parent)
        self.assertEqual(every_election.Post.objects.all().count(), 11)
        self.assertEqual(every_election.YNRElection.objects.all().count(), 10)

    @patch("elections.uk.every_election.requests")
    @freeze_time("2018-02-02")
    def test_import_management_command(self, mock_requests):
        mock_requests.get.side_effect = (
            fake_requests_each_type_of_election_on_one_day
        )

        self.assertEqual(every_election.Ballot.objects.all().count(), 0)
        with self.assertNumQueries(258):
            call_command("uk_create_elections_from_every_election")
        self.assertEqual(every_election.Ballot.objects.all().count(), 15)
        self.assertEqual(
            list(
                every_election.Ballot.objects.all()
                .values_list("ballot_paper_id", flat=True)
                .order_by("ballot_paper_id")
            ),
            [
                "local.adur.buckingham.2019-01-17",
                "mayor.greater-manchester-ca.2019-01-17",
                "mayor.hackney.2019-01-17",
                "naw.c.aberavon.2019-01-17",
                "naw.c.mid-and-west-wales.2019-01-17",
                "naw.r.aberavon.2019-01-17",
                "naw.r.mid-and-west-wales.2019-01-17",
                "nia.lagan-valley.2019-01-17",
                "parl.aberavon.2019-01-17",
                "parl.ynys-mon.2019-01-17",
                "pcc.avon-and-somerset.2019-01-17",
                "sp.c.aberdeen-central.2019-01-17",
                "sp.c.glasgow.2019-01-17",
                "sp.r.aberdeen-central.2019-01-17",
                "sp.r.glasgow.2019-01-17",
            ],
        )

        # Check we set the winner count value
        ballot = every_election.Ballot.objects.get(
            ballot_paper_id="local.adur.buckingham.2019-01-17"
        )
        self.assertEqual(ballot.winner_count, 3)

    @patch("elections.uk.every_election.requests")
    @freeze_time("2018-02-02")
    def test_delete_elections_no_matches(self, mock_requests):
        # import some data
        # just so we've got a non-empty DB
        mock_requests.get.side_effect = (
            fake_requests_each_type_of_election_on_one_day
        )
        call_command("uk_create_elections_from_every_election")
        self.assertEqual(every_election.Ballot.objects.all().count(), 15)
        self.assertEqual(every_election.YNRElection.objects.all().count(), 10)

        # now we're going to delete some stuff
        # but none of the elections in the
        # local_highland fixture
        # match anything we just imported
        mock_requests.get.side_effect = create_mock_with_fixtures(
            {
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?poll_open_date__gte=2018-01-03",
                ): no_results,
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?deleted=1&poll_open_date__gte=2018-01-03",
                ): local_highland,
            }
        )
        # this should finish cleanly without complaining
        call_command("uk_create_elections_from_every_election")

        # nothing in our DB should have changed
        self.assertEqual(every_election.Ballot.objects.all().count(), 15)
        self.assertEqual(every_election.YNRElection.objects.all().count(), 10)

    @patch("elections.uk.every_election.requests")
    @freeze_time("2018-02-02")
    def test_delete_elections_with_matches(self, mock_requests):
        # import some data
        mock_requests.get.side_effect = create_mock_with_fixtures(
            {
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?poll_open_date__gte=2018-01-03",
                ): local_highland,
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?deleted=1&poll_open_date__gte=2018-01-03",
                ): no_results,
            }
        )
        call_command("uk_create_elections_from_every_election")
        self.assertEqual(every_election.Ballot.objects.all().count(), 1)
        self.assertEqual(every_election.YNRElection.objects.all().count(), 1)

        # now we've switched the fixtures round
        # so the records we just imported are deleted in EE
        mock_requests.get.side_effect = create_mock_with_fixtures(
            {
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?poll_open_date__gte=2018-01-03",
                ): no_results,
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?deleted=1&poll_open_date__gte=2018-01-03",
                ): local_highland,
            }
        )
        call_command("uk_create_elections_from_every_election")

        # we should delete the records we just imported
        self.assertEqual(every_election.Ballot.objects.all().count(), 0)
        self.assertEqual(every_election.YNRElection.objects.all().count(), 0)

    @patch("elections.uk.every_election.requests")
    @freeze_time("2018-02-02")
    def test_delete_elections_invalid_input_insert_and_delete(
        self, mock_requests
    ):
        # import some data
        # just so we've got a non-empty DB
        mock_requests.get.side_effect = (
            fake_requests_each_type_of_election_on_one_day
        )
        call_command("uk_create_elections_from_every_election")
        self.assertEqual(every_election.Ballot.objects.all().count(), 15)
        self.assertEqual(every_election.YNRElection.objects.all().count(), 10)

        # this simulates a situation where EE reports
        # the same election/s as deleted and not deleted
        # this makes no sense and shouldn't happen but
        # if it does we should not delete anything
        mock_requests.get.side_effect = create_mock_with_fixtures(
            {
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?poll_open_date__gte=2018-01-03",
                ): local_highland,
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?deleted=1&poll_open_date__gte=2018-01-03",
                ): local_highland,
            }
        )

        # make sure we throw an exception
        with self.assertRaises(Exception):
            call_command("uk_create_elections_from_every_election")

        # we should also roll back the whole transaction
        # so nothing is inserted or deleted
        self.assertEqual(every_election.Ballot.objects.all().count(), 15)
        self.assertEqual(every_election.YNRElection.objects.all().count(), 10)

    @patch("elections.uk.every_election.requests")
    @freeze_time("2018-02-02")
    def test_delete_elections_invalid_input_non_empty_election(
        self, mock_requests
    ):
        # import some data
        mock_requests.get.side_effect = create_mock_with_fixtures(
            {
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?poll_open_date__gte=2018-01-03",
                ): local_highland,
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?deleted=1&poll_open_date__gte=2018-01-03",
                ): no_results,
            }
        )
        call_command("uk_create_elections_from_every_election")
        self.assertEqual(every_election.Ballot.objects.all().count(), 1)
        self.assertEqual(every_election.YNRElection.objects.all().count(), 1)

        # this simulates a situation where EE reports
        # a ballot as current but its parent election as
        # deleted this makes no sense and shouldn't happen
        # but if it does we should not delete anything
        current_elections = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [local_highland["results"][1]],
        }
        deleted_elections = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [local_highland["results"][0]],
        }
        mock_requests.get.side_effect = create_mock_with_fixtures(
            {
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?poll_open_date__gte=2018-01-03",
                ): current_elections,
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?deleted=1&poll_open_date__gte=2018-01-03",
                ): deleted_elections,
            }
        )

        # make sure we throw an exception
        with self.assertRaises(Exception):
            call_command("uk_create_elections_from_every_election")

        # we should also roll back the whole transaction
        # so nothing is inserted or deleted
        self.assertEqual(every_election.Ballot.objects.all().count(), 1)
        self.assertEqual(every_election.YNRElection.objects.all().count(), 1)

    @patch("elections.uk.every_election.requests")
    @freeze_time("2018-02-02")
    def test_delete_elections_with_related_membership(self, mock_requests):
        # import some data
        mock_requests.get.side_effect = create_mock_with_fixtures(
            {
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?poll_open_date__gte=2018-01-03",
                ): local_highland,
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?deleted=1&poll_open_date__gte=2018-01-03",
                ): no_results,
            }
        )
        call_command("uk_create_elections_from_every_election")
        self.assertEqual(every_election.Ballot.objects.all().count(), 1)
        self.assertEqual(every_election.YNRElection.objects.all().count(), 1)

        # create a membership which references the PEE we just imported
        MembershipFactory(
            person=PersonFactory.create(id=2009, name="Tessa Jowell"),
            ballot=every_election.Ballot.objects.all()[0],
        )

        # now we've switched the fixtures round
        # so the records we just imported are deleted in EE
        mock_requests.get.side_effect = create_mock_with_fixtures(
            {
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?poll_open_date__gte=2018-01-03",
                ): no_results,
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?deleted=1&poll_open_date__gte=2018-01-03",
                ): local_highland,
            }
        )
        # make sure we throw an exception
        with self.assertRaises(Exception):
            call_command("uk_create_elections_from_every_election")

        # we should also roll back the whole transaction so nothing is deleted
        self.assertEqual(every_election.Ballot.objects.all().count(), 1)
        self.assertEqual(every_election.YNRElection.objects.all().count(), 1)

    @patch("elections.uk.every_election.requests")
    @freeze_time("2018-02-02")
    def test_import_post_duplicate_slugs(self, mock_requests):
        """
        Regression test to check that a post with duplicate names

        :param mock_requests:
        :return:
        """
        mock_requests.get.side_effect = create_mock_with_fixtures(
            {
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?poll_open_date__gte=2018-01-03",
                ): duplicate_post_names,
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?deleted=1&poll_open_date__gte=2018-01-03",
                ): local_highland,
            }
        )
        call_command("uk_create_elections_from_every_election")
        post_a, post_b = Post.objects.all().order_by(
            "-slug", "-organization__name"
        )

        self.assertEqual(post_a.slug, "st-michaels")
        self.assertEqual(post_a.identifier, "SUR:st-michaels")
        self.assertEqual(post_a.start_date, "2019-05-02")
        self.assertEqual(
            post_a.organization.name, "Surrey Heath Borough Council"
        )

        self.assertEqual(post_b.slug, "st-michaels")
        self.assertEqual(post_b.identifier, "ALL:st-michaels")
        self.assertEqual(post_a.start_date, "2019-05-02")
        self.assertEqual(post_b.organization.name, "Allerdale Borough Council")

    @patch("elections.uk.every_election.requests")
    @freeze_time("2019-05-02")
    def test_import_post_pre_and_post_gss(self, mock_requests):
        """
        Test that posts imported before GSS codes aren't duplicated
        at the point we have GSS codes for them in EE
        """

        mock_requests.get.side_effect = create_mock_with_fixtures(
            {
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?poll_open_date__gte=2019-04-02",
                ): pre_gss_result,
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?deleted=1&poll_open_date__gte=2019-04-02",
                ): local_highland,
            }
        )

        self.assertEqual(Post.objects.count(), 0)
        call_command("uk_create_elections_from_every_election")
        self.assertEqual(Post.objects.count(), 1)

        mock_requests.get.side_effect = create_mock_with_fixtures(
            {
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?poll_open_date__gte=2019-04-02",
                ): post_gss_result,
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?deleted=1&poll_open_date__gte=2019-04-02",
                ): local_highland,
            }
        )

        call_command("uk_create_elections_from_every_election")
        self.assertEqual(Post.objects.count(), 1)

    @patch("elections.uk.every_election.requests")
    @freeze_time("2019-05-02")
    def test_adds_replaces(self, mock_requests):
        "local.highland.wester-ross-strathpeffer-and-lochalsh.by.2018-12-06"
        # PostFactory.create()
        org = OrganizationFactory(name="Highland Council")
        election = ElectionFactory.create(
            slug="local.highland.2017-12-06",
            election_date="2017-12-06",
            organization=org,
        )
        PostFactory.create(
            elections=(election,),
            slug="wester-ross-strathpeffer-and-lochalsh.by",
            label="Councillor",
            organization=org,
        )

        self.assertEqual(Ballot.objects.all().count(), 1)
        old_ballot = Ballot.objects.get()

        mock_requests.get.side_effect = create_mock_with_fixtures(
            {
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?poll_open_date__gte=2019-04-02",
                ): replaced_election,
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?deleted=1&poll_open_date__gte=2019-04-02",
                ): no_results,
            }
        )

        call_command("uk_create_elections_from_every_election")
        self.assertEqual(Ballot.objects.all().count(), 2)
        new_ballot = Ballot.objects.order_by("pk").last()
        self.assertEqual(new_ballot.replaces, old_ballot)

    @patch("elections.uk.every_election.requests")
    @freeze_time("2019-05-02")
    def test_create_duplicate_post_election(self, mock_requests):
        self.assertEqual(Ballot.objects.all().count(), 0)

        mock_requests.get.side_effect = create_mock_with_fixtures(
            {
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?poll_open_date__gte=2019-04-02",
                ): duplicate_post_and_election,
                urljoin(
                    EE_BASE_URL,
                    "/api/elections/?deleted=1&poll_open_date__gte=2019-04-02",
                ): no_results,
            }
        )

        call_command("uk_create_elections_from_every_election")
        self.assertEqual(Ballot.objects.all().count(), 2)
