import datetime
from copy import deepcopy
from typing import Dict, List
from unittest import mock
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

import pytest
from candidates.models import Ballot
from candidates.tests.factories import (
    BallotPaperFactory,
    ElectionFactory,
    MembershipFactory,
    OrganizationFactory,
    PostFactory,
)
from django.conf import settings
from django.core.management import call_command
from django.utils import timezone
from django_webtest import WebTest
from elections.models import Election
from elections.uk import every_election
from freezegun import freeze_time
from mock import Mock, patch
from parties.tests.factories import PartyFactory
from people.tests.factories import PersonFactory
from popolo.models import Post

from .ee_import_results import (
    current_elections,
    current_elections_page_2,
    current_elections_parents,
    duplicate_post_and_election,
    duplicate_post_and_election_parents,
    duplicate_post_names,
    duplicate_post_names_parent,
    each_type_of_election_on_one_day,
    each_type_of_election_on_one_day_parents,
    get_changing_identifier_code_result_parent,
    local_highland,
    local_highland_parent,
    no_results,
    post_gss_result,
    pre_gss_result,
    replaced_election,
    replaced_election_parents,
)

EE_BASE_URL = getattr(
    settings, "EE_BASE_URL", "https://elections.democracyclub.org.uk/"
)


def make_elections_url_with_params(params, path="/api/elections/"):
    base_url = urljoin(
        EE_BASE_URL,
        path,
    )
    return f"{base_url}?{urlencode(params)}"


def make_per_election_fixtures_from_pages(pages: List[Dict], deleted=False):
    fixtures = {}
    for page in pages:
        for election in page["results"]:
            id_parts = election["election_id"].split(".")
            parent_id = ".".join(id_parts[:2])
            poll_open_date = id_parts[-1]
            params = {
                "poll_open_date": poll_open_date,
                "election_id_regex": parent_id,
            }
            if deleted:
                params["deleted"] = "1"
            url = make_elections_url_with_params(params)
            if url not in fixtures:
                fixtures[url] = {
                    "count": 0,
                    "next": None,
                    "previous": None,
                    "results": [],
                }
            fixtures[url]["results"].append(election)
            fixtures[url]["count"] = len(fixtures[url]["results"])
    return fixtures


def create_mock_with_fixtures(
    params: dict,
    parents,
    ballot_pages,
    deleted=None,
    modified=False,
    extra_urls=None,
):
    fixtures = {}
    if not deleted:
        deleted = no_results
    params.update(exclude_ref_regex_param)
    if not modified:
        params["identifier_type"] = "election"
    parent_url = make_elections_url_with_params(params)

    fixtures[parent_url] = parents
    fixtures.update(
        make_per_election_fixtures_from_pages(
            ballot_pages,
        )
    )

    deleted_params = {"deleted": 1}

    deleted_parent_params = params.copy()
    deleted_parent_params.update(deleted_params)
    deleted_parent_url = make_elections_url_with_params(deleted_parent_params)
    fixtures[deleted_parent_url] = deleted

    fixtures.update(
        make_per_election_fixtures_from_pages([deleted], deleted=True)
    )

    for params, fixture in extra_urls or []:
        if election_id := params.get("election_id", None):
            url = make_elections_url_with_params(
                {}, f"/api/elections/{election_id}"
            )
            fixtures[url] = fixture

    def mock(url):
        url_params = parse_qs(urlparse(url).query)
        for fixture_url, fixture in fixtures.items():
            params = parse_qs(urlparse(fixture_url).query)
            if params == url_params:
                return Mock(
                    **{"json.return_value": fixture, "status_code": 200}
                )
        raise ValueError(f"Can't find {url_params} in {fixtures.keys()}")

    return mock


exclude_ref_regex_param = {"exclude_election_id_regex": r"^ref\..*"}

fake_requests_current_elections = create_mock_with_fixtures(
    {"poll_open_date__gte": "2018-01-03"},
    current_elections_parents,
    [current_elections, current_elections_page_2],
)

fake_requests_each_type_of_election_on_one_day = create_mock_with_fixtures(
    {"poll_open_date__gte": "2018-01-03"},
    parents=each_type_of_election_on_one_day_parents,
    ballot_pages=[each_type_of_election_on_one_day],
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
        query_args = {"poll_open_date": "2019-01-17", "current": "True"}
        mock_requests.get.side_effect = create_mock_with_fixtures(
            query_args,
            current_elections_parents,
            [current_elections, current_elections_page_2],
        )
        self.ee_importer = every_election.EveryElectionImporter(query_args)
        self.ee_importer.build_election_tree()

        for ballot_id, election_dict in self.ee_importer.ballot_ids.items():
            parent = self.ee_importer.get_parent(ballot_id)
            election_dict.get_or_create_ballot(parent=parent)
        self.assertEqual(every_election.Post.objects.all().count(), 189)
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
            {"poll_open_date__gte": "2018-01-03"},
            no_results,
            ballot_pages=[],
            deleted=local_highland,
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
            {"poll_open_date__gte": "2018-01-03"},
            local_highland_parent,
            [local_highland],
        )
        call_command("uk_create_elections_from_every_election")
        self.assertEqual(every_election.Ballot.objects.all().count(), 1)
        self.assertEqual(every_election.YNRElection.objects.all().count(), 1)

        # now we've switched the fixtures round
        # so the records we just imported are deleted in EE
        mock_requests.get.side_effect = create_mock_with_fixtures(
            {"poll_open_date__gte": "2018-01-03"},
            no_results,
            [no_results],
            # TODO: mock all URLS for deleted results
            deleted=local_highland,
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
            {"poll_open_date__gte": "2018-01-03"},
            local_highland_parent,
            [local_highland],
            deleted=local_highland,
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
            {"poll_open_date__gte": "2018-01-03"},
            parents=local_highland_parent,
            ballot_pages=[local_highland],
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
            {"poll_open_date__gte": "2018-01-03"},
            parents=local_highland_parent,
            ballot_pages=[current_elections],
            deleted=deleted_elections,
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
            {"poll_open_date__gte": "2018-01-03"},
            local_highland_parent,
            [local_highland],
        )
        call_command("uk_create_elections_from_every_election")
        self.assertEqual(every_election.Ballot.objects.all().count(), 1)
        self.assertEqual(every_election.YNRElection.objects.all().count(), 1)

        # create a membership which references the PEE we just imported
        MembershipFactory(
            person=PersonFactory.create(id=2009, name="Tessa Jowell"),
            ballot=every_election.Ballot.objects.all()[0],
            party=PartyFactory(),
        )

        # now we've switched the fixtures round
        # so the records we just imported are deleted in EE
        mock_requests.get.side_effect = create_mock_with_fixtures(
            {"poll_open_date__gte": "2018-01-03"},
            no_results,
            [no_results],
            deleted=local_highland,
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
            {"poll_open_date__gte": "2018-01-03"},
            duplicate_post_names_parent,
            [duplicate_post_names],
            deleted=no_results,
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
            {"poll_open_date__gte": "2019-04-02"},
            get_changing_identifier_code_result_parent,
            [pre_gss_result],
            deleted=no_results,
        )
        self.assertEqual(Post.objects.count(), 0)
        call_command("uk_create_elections_from_every_election")
        self.assertEqual(Post.objects.count(), 1)

        mock_requests.get.side_effect = create_mock_with_fixtures(
            {"poll_open_date__gte": "2019-04-02"},
            get_changing_identifier_code_result_parent,
            [post_gss_result],
            deleted=no_results,
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
            territory_code="SCT",
        )

        self.assertEqual(Ballot.objects.all().count(), 1)
        old_ballot = Ballot.objects.get()

        mock_requests.get.side_effect = create_mock_with_fixtures(
            {"poll_open_date__gte": "2019-04-02"},
            parents=replaced_election_parents,
            ballot_pages=[replaced_election],
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
            {"poll_open_date__gte": "2019-04-02"},
            duplicate_post_and_election_parents,
            [duplicate_post_and_election],
        )

        call_command("uk_create_elections_from_every_election")
        self.assertEqual(Ballot.objects.all().count(), 2)

    @patch("elections.uk.every_election.requests")
    @patch(
        "elections.uk.management.commands.uk_create_elections_from_every_election.Command.get_latest_ee_modified_datetime"
    )
    @freeze_time("2018-02-02")
    def test_get_parent_when_missing_from_tree(
        self, ee_modified_datetime, mock_requests
    ):
        ee_modified_datetime.return_value = datetime.datetime(
            year=2018, month=2, day=2
        )
        self.assertEqual(Ballot.objects.all().count(), 0)
        self.assertEqual(Election.objects.all().count(), 0)
        missing_parent = deepcopy(local_highland)
        del missing_parent["results"][0]
        mock_requests.get.side_effect = create_mock_with_fixtures(
            {"modified": "2018-02-02T00:00:00"},
            missing_parent,
            [missing_parent],
            modified=True,
            extra_urls=[
                (
                    {"election_id": "local.highland.2018-12-06"},
                    local_highland["results"][0],
                )
            ],
        )
        call_command(
            "uk_create_elections_from_every_election", recently_updated=True
        )
        self.assertEqual(Ballot.objects.all().count(), 1)
        self.assertEqual(Election.objects.all().count(), 1)


class TestRecenlyUpdated:
    @pytest.fixture
    def command_obj(self):
        from elections.uk.management.commands.uk_create_elections_from_every_election import (
            Command,
        )

        return Command()

    @pytest.mark.django_db
    def test_get_latest_ee_modified_datetime(self, command_obj):
        """
        Test that the latest ee_modified timestamp is returned from
        either the Ballot or Election
        """
        earlier = timezone.datetime(
            2021, 9, 20, 0, 0, 0, tzinfo=datetime.timezone.utc
        )
        later = timezone.datetime(
            2021, 10, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
        )
        ballot = BallotPaperFactory(
            ee_modified=later, election__ee_modified=earlier
        )
        result = command_obj.get_latest_ee_modified_datetime()

        assert result == ballot.ee_modified
        assert result != ballot.election.ee_modified

        # change so that the election was updated more recently
        ballot.ee_modified = earlier
        ballot.election.ee_modified = later
        ballot.save()

        assert result == ballot.election.ee_modified
        assert result != ballot.ee_modified


class TestEEElection:
    @patch("elections.uk.every_election.EEElection.get_or_create_election")
    @patch("elections.uk.every_election.EEElection.get_or_create_post")
    def test_get_or_create_ballot(
        self, mock_get_or_create_post, mock_get_or_create_election
    ):
        """
        The purpose of this test is to ensure that we have a check for
        the data that is stored from EE response when we create a
        ballot. If we begin to capture a new field, or remove one,
        then this test will fail. This is mainly to act as a safety
        net so that a field that we rely on elsewhere is not removed
        that might otherwise go unnoticed e.g. the 'ee_modifoed' field
        """
        modified = timezone.datetime(
            2021, 10, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
        )
        data = {
            "group": "local.2021-10-21",
            "seats_contested": 1,
            "election_id": "local.birmingham.yardley-east.by.2021-10-21",
            "cancelled": False,
            "replaces": None,
            "modified": modified,
            "voting_system": {"slug": "FPTP"},
        }
        ee_election = every_election.EEElection(data)
        ee_election.post_object = mock.MagicMock()
        parent = every_election.EEElection({"election_id": "local.2021-10-21"})
        parent.election_object = mock.MagicMock()

        result = ("ballot_obj", "created")
        with patch.object(
            Ballot.objects, "update_or_create", return_value=result
        ) as mock_update_or_create:
            ee_election.get_or_create_ballot(parent=parent)
            mock_update_or_create.assert_called_once_with(
                ballot_paper_id="local.birmingham.yardley-east.by.2021-10-21",
                defaults={
                    "post": ee_election.post_object,
                    "election": parent.election_object,
                    "winner_count": 1,
                    "cancelled": False,
                    "replaces": None,
                    "tags": {},
                    "voting_system": "FPTP",
                    "ee_modified": modified,
                },
            )
            mock_get_or_create_post.assert_called_once()
            mock_get_or_create_election.assert_called_once()

    @patch("elections.uk.every_election.EEElection.get_or_create_organisation")
    def test_get_or_create_election(self, mock_get_or_create_org):
        """
        The purpose of this test is to ensure that we have a check for
        the data that is stored from EE response when we create a
        ballot. If we begin to capture a new field, or remove one,
        then this test will fail. This is mainly to act as a safety
        net so that a field that we rely on elsewhere is not removed
        that might otherwise go unnoticed e.g. the 'ee_modifoed' field
        """
        modified = timezone.datetime(
            2021, 10, 1, 0, 0, 0, tzinfo=datetime.timezone.utc
        )
        poll_open_date = timezone.datetime(2021, 10, 6).date()
        data = {
            "election_id": "local.2021-10-21",
            "poll_open_date": poll_open_date,
            "current": True,
            "election_type": {"name": "Local elections"},
            "election_title": "Local elections",
            "modified": modified,
            "voting_system": {"uses_party_lists": False},
        }
        mock_org = mock.MagicMock()
        mock_get_or_create_org.return_value = [mock_org]
        ee_election = every_election.EEElection(data)

        with patch.object(
            Election.objects, "update_or_create"
        ) as mock_update_or_create:
            mock_update_or_create.return_value = ("election_obj", "created")
            ee_election.get_or_create_election()
            mock_update_or_create.assert_called_once_with(
                slug="local.2021-10-21",
                election_date=poll_open_date,
                defaults={
                    "current": True,
                    "candidate_membership_role": "Candidate",
                    "for_post_role": "Local elections",
                    "show_official_documents": True,
                    "name": "Local elections",
                    "party_lists_in_use": False,
                    "organization": mock_org,
                    "ee_modified": modified,
                },
            )
            mock_get_or_create_org.assert_called_once()
