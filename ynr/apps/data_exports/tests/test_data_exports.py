import csv
from urllib.parse import urlencode

from candidates.models import Ballot
from candidates.tests.uk_examples import UK2015ExamplesMixin
from data_exports.csv_fields import get_core_fieldnames
from data_exports.models import MaterializedMemberships
from data_exports.templatetags.data_field_value import data_cell
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from people.models import Person


def csv_to_dicts(csv_data):
    return csv.DictReader(csv_data.decode("utf-8").splitlines())


def csv_url(query_params):
    query_params["download"] = 1
    return f"{reverse('data_export')}?{urlencode(query_params)}"


class TestMaterializedMemberships(UK2015ExamplesMixin, TestCase):
    def test_materialized_view_populated(self):
        self.create_lots_of_candidates(
            self.earlier_election, ((self.labour_party, 16), (self.ld_party, 8))
        )
        self.assertEqual(MaterializedMemberships.objects.count(), 0)
        MaterializedMemberships.refresh_view()
        self.assertEqual(MaterializedMemberships.objects.count(), 24)

    def test_csv_simple_memberships(self):
        req = self.client.get(csv_url({}))
        csv_data = csv_to_dicts(req.content)
        self.assertEqual(
            csv_data.fieldnames,
            get_core_fieldnames(),
        )

    def test_extra_fields_show_in_export(self):
        req = self.client.get(csv_url({"extra_fields": "votes_cast"}))
        csv_data = csv_to_dicts(req.content)
        self.assertTrue(
            "votes_cast" in csv_data.fieldnames,
        )

    def test_random_header_cant_be_added(self):
        req = self.client.get(csv_url({"extra_fields": "made_up"}))
        csv_data = csv_to_dicts(req.content)
        self.assertFalse(
            "made_up" in csv_data.fieldnames,
        )

    def test_core_fields_row(self):
        self.create_lots_of_candidates(
            self.earlier_election, ((self.labour_party, 16), (self.ld_party, 8))
        )
        MaterializedMemberships.refresh_view()

        req = self.client.get(csv_url({}))
        csv_data = csv_to_dicts(req.content)
        expected_person_id = Person.objects.all().first().pk
        self.assertDictEqual(
            next(csv_data),
            {
                "ballot_paper_id": "parl.14419.2010-05-06",
                "cancelled_poll": "f",
                "election_current": "f",
                "election_date": str(self.earlier_election.election_date),
                "election_id": "parl.2010-05-06",
                "party_id": "PP53",
                "party_name": "Labour Party",
                "person_id": f"{expected_person_id}",
                "person_name": f"John Doe {expected_person_id}",
                "post_label": "Member of Parliament for Edinburgh East",
                "seats_contested": "1",
            },
        )

    def test_data_export_frontend(self):
        self.create_lots_of_candidates(
            self.earlier_election, ((self.labour_party, 16), (self.ld_party, 8))
        )
        call_command("update_data_export_view")
        resp = self.client.get("/data/")
        self.assertFalse(resp.context["page_obj"].has_previous())
        self.assertFalse(resp.context["page_obj"].has_next())
        self.assertEqual(len(resp.context["page_obj"].object_list), 24)
        a_person = Person.objects.first()
        html_content = resp.content.decode("utf8")
        self.assertInHTML(
            f'<a href="/person/{a_person.pk}">{a_person.pk}</a>', html_content
        )

    def test_basic_filters(self):
        self.create_lots_of_candidates(
            self.earlier_election, ((self.labour_party, 16), (self.ld_party, 8))
        )
        call_command("update_data_export_view")
        ballot_paper_id = (
            Ballot.objects.exclude(membership=None).first().ballot_paper_id
        )
        resp = self.client.get("/data/")
        self.assertEqual(len(resp.context["page_obj"].object_list), 24)
        resp = self.client.get("/data/?ballot_paper_id=" + ballot_paper_id)
        self.assertEqual(len(resp.context["page_obj"].object_list), 6)

    def test_data_call_template_tag(self):
        value = {"person_id": 12345, "party_name": None}
        self.assertEqual(
            data_cell("person_id", value), '<a href="/person/12345">12345</a>'
        )
        self.assertEqual(data_cell("party_name", value), "")

    def test_select_whole_group(self):
        self.create_lots_of_candidates(
            self.earlier_election, ((self.labour_party, 16), (self.ld_party, 8))
        )
        MaterializedMemberships.refresh_view()

        req = self.client.get(csv_url({}))
        csv_data = csv_to_dicts(req.content)
        headers = list(next(csv_data).keys())
        self.assertListEqual(
            headers,
            [
                "person_id",
                "person_name",
                "election_id",
                "ballot_paper_id",
                "election_date",
                "election_current",
                "party_name",
                "party_id",
                "post_label",
                "cancelled_poll",
                "seats_contested",
            ],
        )

        req = self.client.get(csv_url({"field_group": "results"}))
        csv_data = csv_to_dicts(req.content)
        headers = list(next(csv_data).keys())
        self.assertListEqual(
            headers,
            [
                "person_id",
                "person_name",
                "election_id",
                "ballot_paper_id",
                "election_date",
                "election_current",
                "party_name",
                "party_id",
                "post_label",
                "cancelled_poll",
                "seats_contested",
                "votes_cast",
                "elected",
                "tied_vote_winner",
                "rank",
                "turnout_reported",
                "spoilt_ballots",
                "total_electorate",
                "turnout_percentage",
                "results_source",
            ],
        )

    def test_complex_filter(self):
        self.create_lots_of_candidates(
            self.earlier_election, ((self.labour_party, 16), (self.ld_party, 8))
        )
        MaterializedMemberships.refresh_view()

        req = self.client.get(
            csv_url(
                {
                    # election_date=&ballot_paper_id=&election_id=parl&party_id=&cancelled=&
                    "format": "csv",
                    "field_group": "election",
                }
            )
        )
        csv_data = csv_to_dicts(req.content)
        headers = list(next(csv_data).keys())
        self.assertListEqual(
            headers,
            [
                "person_id",
                "person_name",
                "election_id",
                "ballot_paper_id",
                "election_date",
                "election_current",
                "party_name",
                "party_id",
                "post_label",
                "cancelled_poll",
                "seats_contested",
                "by_election",
                "gss",
                "post_id",
                "candidates_locked",
                "nuts1",
                "organisation_name",
            ],
        )
