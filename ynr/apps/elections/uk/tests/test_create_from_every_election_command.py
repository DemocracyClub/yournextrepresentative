from mock import patch, Mock

from django.utils.six.moves.urllib_parse import urljoin
from django.core.management import call_command
from django.conf import settings

from django_webtest import WebTest

from .ee_import_results import (
    current_elections, current_elections_page_2,
    each_type_of_election_on_one_day
)
from elections.uk import every_election
from candidates.models import check_constraints


def fake_requests_for_every_election(url, *args, **kwargs):
    """Return reduced EE output for some known URLs"""

    EE_BASE_URL = getattr(
        settings, "EE_BASE_URL", "https://elections.democracyclub.org.uk/")
    result = None

    if url == urljoin(EE_BASE_URL, 'api/elections/?current=True'):
        status_code = 200
        result = current_elections

    if url == urljoin(EE_BASE_URL, '/api/elections/?current=True&limit=100&offset=100'):  # noqa
        status_code = 200
        result = current_elections_page_2

    if url == urljoin(EE_BASE_URL, '/api/elections/?current=True&poll_open_date=2019-01-17'):  # noqa
        status_code = 200
        result = each_type_of_election_on_one_day

    if not result:
        raise Exception("URL that hasn't been mocked yet: " + url)

    return Mock(**{
        'json.return_value': result,
        'status_code': status_code
    })


class EE_ImporterTest(WebTest):

    @patch('elections.uk.every_election.requests')
    def setUp(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_every_election

        self.ee_importer = every_election.EveryElectionImporter()
        self.ee_importer.build_election_tree()


        self.parent_id = 'local.brent.2018-02-22'  # they're good elections
        self.child_id = 'local.brent.alperton.2018-02-22'


    def test_ee_importer_build_tree(self):
        self.assertEqual(len(self.ee_importer.election_tree.keys()), 200)
        self.assertEqual(len(self.ee_importer.ballot_ids.keys()), 189)

        self.assertEqual(
            type(self.ee_importer.election_tree[self.parent_id]),
            every_election.EEElection
        )

    def test_ee_importer_parent_from_string(self):
        parent = self.ee_importer.get_parent(self.child_id)
        self.assertEqual(parent['election_id'], self.parent_id)

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
        self.assertEqual(
            election.election_object.name,
            "Brent local election"
        )

        self.assertEqual(
            election.election_object.party_lists_in_use,
            False
        )
        self.assertEqual(
            election.organization_object.name,
            'London Borough of Brent'
        )
        self.assertTrue(election.organization_created)

    def test_create_organization_from_election_dict(self):
        election = self.ee_importer.election_tree[self.parent_id]

        # Create and election from the API dict and verify it's there
        election.get_or_create_organisation()
        self.assertTrue(election.organization_created)

        # Check other info about the election
        self.assertEqual(
            election.organization_object.name,
            "London Borough of Brent"
        )
        self.assertEqual(
            election.organization_object.extra.slug,
            "local-authority:brent"
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
        self.assertEqual(every_election.PostExtra.objects.all().count(), 0)
        election = self.ee_importer.election_tree[self.child_id]
        election.get_or_create_post()
        self.assertTrue(election.post_created)
        election.get_or_create_post()
        self.assertFalse(election.post_created)
        self.assertEqual(every_election.Post.objects.all().count(), 1)
        self.assertEqual(every_election.PostExtra.objects.all().count(), 1)

        self.assertEqual(
            election.party_set_object.name,
            "Great Britain"
        )
        self.assertEqual(
            election.post_object.label,
            "Alperton"
        )
        self.assertEqual(check_constraints(), [])

    def test_create_post__election_from_ballot_id_dict(self):
        self.assertEqual(every_election.Post.objects.all().count(), 0)
        self.assertEqual(every_election.PostExtra.objects.all().count(), 0)
        self.assertEqual(every_election.YNRElection.objects.all().count(), 0)
        election = self.ee_importer.election_tree[self.child_id]

        parent = self.ee_importer.get_parent(self.child_id)
        election.get_or_create_post_election(parent=parent)

        self.assertTrue(election.post_created)
        with self.assertNumQueries(0):
            election.get_or_create_post_election(parent=parent)
            election.get_or_create_post()
        self.assertFalse(election.post_created)

        self.assertEqual(every_election.Post.objects.all().count(), 1)
        self.assertEqual(every_election.PostExtra.objects.all().count(), 1)

        self.assertEqual(
            election.party_set_object.name,
            "Great Britain"
        )
        self.assertEqual(
            election.post_object.label,
            "Alperton"
        )
        self.assertEqual(check_constraints(), [])

    def test_create_many_elections_and_posts(self):
        for ballot_id, election_dict in self.ee_importer.ballot_ids.items():
            parent = self.ee_importer.get_parent(ballot_id)
            election_dict.get_or_create_post_election(parent=parent)
        self.assertEqual(every_election.PostExtra.objects.all().count(), 189)
        self.assertEqual(every_election.YNRElection.objects.all().count(), 10)
        self.assertEqual(check_constraints(), [])

    @patch('elections.uk.every_election.requests')
    def test_create_from_all_elections(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_every_election
        query_args = {
            'poll_open_date': '2019-01-17',
            'current': 'True',
        }
        self.ee_importer = every_election.EveryElectionImporter(query_args)
        self.ee_importer.build_election_tree()

        for ballot_id, election_dict in self.ee_importer.ballot_ids.items():
            parent = self.ee_importer.get_parent(ballot_id)
            election_dict.get_or_create_post_election(parent=parent)
        self.assertEqual(every_election.PostExtra.objects.all().count(), 11)
        self.assertEqual(every_election.YNRElection.objects.all().count(), 10)
        self.assertEqual(check_constraints(), [])

    @patch('elections.uk.every_election.requests')
    def test_import_management_command(self, mock_requests):
        mock_requests.get.side_effect = lambda m: Mock(**{
            'json.return_value': each_type_of_election_on_one_day,
            'status_code': 200
        })

        self.assertEqual(every_election.PostExtra.objects.all().count(), 0)
        with self.assertNumQueries(300):
            call_command('uk_create_elections_from_every_election')
        self.assertEqual(
            every_election.PostExtraElection.objects.all().count(),
            15
        )
        self.assertEqual(
            list(every_election.PostExtraElection.objects.all().values_list(
                'ballot_paper_id', flat=True).order_by('ballot_paper_id')),
            [
                'local.adur.buckingham.2019-01-17',
                'mayor.greater-manchester-ca.2019-01-17',
                'mayor.hackney.2019-01-17',
                'naw.c.aberavon.2019-01-17',
                'naw.c.mid-and-west-wales.2019-01-17',
                'naw.r.aberavon.2019-01-17',
                'naw.r.mid-and-west-wales.2019-01-17',
                'nia.lagan-valley.2019-01-17',
                'parl.aberavon.2019-01-17',
                'parl.ynys-mon.2019-01-17',
                'pcc.avon-and-somerset.2019-01-17',
                'sp.c.aberdeen-central.2019-01-17',
                'sp.c.glasgow.2019-01-17',
                'sp.r.aberdeen-central.2019-01-17',
                'sp.r.glasgow.2019-01-17',
            ]
        )

        # Check we set the winner count value
        pee = every_election.PostExtraElection.objects.get(
            ballot_paper_id='local.adur.buckingham.2019-01-17',
        )
        self.assertEqual(pee.winner_count, 3)
