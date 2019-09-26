from datetime import date, timedelta

from django.conf import settings
from django.utils.six.moves.urllib_parse import urljoin
from django_webtest import WebTest
from mock import Mock, patch

from candidates.tests.factories import (
    ElectionFactory,
    MembershipFactory,
    ParliamentaryChamberFactory,
    PostFactory,
)
from candidates.tests.uk_examples import UK2015ExamplesMixin
from compat import text_type
from elections.uk.tests.ee_postcode_results import (
    ee_se240ag_result,
    ee_sw1a1aa_result,
)
from people.tests.factories import PersonFactory


def fake_requests_for_every_election(url, *args, **kwargs):
    """Return reduced EE output for some known URLs"""

    EE_BASE_URL = getattr(
        settings, "EE_BASE_URL", "https://elections.democracyclub.org.uk/"
    )
    if url == urljoin(EE_BASE_URL, "/api/elections/?postcode=se240ag"):
        status_code = 200
        json_result = ee_se240ag_result
    elif url == urljoin(EE_BASE_URL, "/api/elections/?postcode=sw1a1aa"):
        status_code = 200
        json_result = ee_sw1a1aa_result
    elif url == urljoin(EE_BASE_URL, "/api/elections/?postcode=cb28rq"):
        status_code = 404
        json_result = {
            "code": 404,
            "error": "No Postcode matches the given query.",
        }
    else:
        raise Exception("URL that hasn't been mocked yet: " + url)
    return Mock(
        **{"json.return_value": json_result, "status_code": status_code}
    )


@patch("elections.uk.geo_helpers.requests")
class TestUpcomingElectionsAPI(UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()

    def test_empty_results(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_every_election
        response = self.app.get("/upcoming-elections/?postcode=SW1A+1AA")

        output = response.json
        self.assertEqual(output, [])

    def test_results_for_past_elections(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_every_election
        response = self.app.get("/upcoming-elections/?postcode=SE24+0AG")

        output = response.json
        self.assertEqual(output, [])

    def _setup_data(self):
        one_day = timedelta(days=1)
        self.future_date = date.today() + one_day
        london_assembly = ParliamentaryChamberFactory.create(
            slug="london-assembly", name="London Assembly"
        )
        election_lac = ElectionFactory.create(
            slug="gla.c.2016-05-05",
            organization=london_assembly,
            name="2016 London Assembly Election (Constituencies)",
            election_date=self.future_date.isoformat(),
        )
        self.election_gla = ElectionFactory.create(
            slug="gla.a.2016-05-05",
            organization=london_assembly,
            name="2016 London Assembly Election (Additional)",
            election_date=self.future_date.isoformat(),
        )
        PostFactory.create(
            elections=(election_lac,),
            organization=london_assembly,
            slug="lambeth-and-southwark",
            label="Assembly Member for Lambeth and Southwark",
        )
        self.post = PostFactory.create(
            elections=(self.election_gla,),
            organization=london_assembly,
            slug="london",
            label="Assembly Member",
        )

    def test_results_for_upcoming_elections(self, mock_requests):
        self._setup_data()

        mock_requests.get.side_effect = fake_requests_for_every_election
        response = self.app.get("/upcoming-elections/?postcode=SE24+0AG")
        output = response.json
        self.assertEqual(len(output), 2)

        self.maxDiff = None
        expected = [
            {
                "organization": "London Assembly",
                "election_date": text_type(self.future_date.isoformat()),
                "election_id": "gla.c.2016-05-05",
                "election_name": "2016 London Assembly Election (Constituencies)",
                "post_name": "Assembly Member for Lambeth and Southwark",
                "post_slug": "lambeth-and-southwark",
            },
            {
                "organization": "London Assembly",
                "election_date": text_type(self.future_date.isoformat()),
                "election_id": "gla.a.2016-05-05",
                "election_name": "2016 London Assembly Election (Additional)",
                "post_name": "Assembly Member",
                "post_slug": "london",
            },
        ]

        self.assertEqual(expected, output)

    def test_results_for_candidates_for_postcode(self, mock_requests):
        self._setup_data()

        person = PersonFactory.create(id=2009, name="Tessa Jowell")

        MembershipFactory.create(
            person=person,
            post=self.post,
            party=self.labour_party,
            ballot=self.election_gla.ballot_set.get(post=self.post),
        )
        membership_pk = person.memberships.first().pk

        self.maxDiff = None

        mock_requests.get.side_effect = fake_requests_for_every_election
        response = self.app.get(
            "/api/v0.9/candidates_for_postcode/?postcode=SE24+0AG"
        )

        output = response.json
        self.assertEqual(len(output), 2)
        expected = [
            {
                "candidates": [],
                "election_date": text_type(self.future_date.isoformat()),
                "election_id": "gla.c.2016-05-05",
                "election_name": "2016 London Assembly Election (Constituencies)",
                "organization": "London Assembly",
                "post": {
                    "post_candidates": None,
                    "post_name": "Assembly Member for Lambeth and Southwark",
                    "post_slug": "lambeth-and-southwark",
                },
            },
            {
                "candidates": [
                    {
                        "birth_date": "",
                        "contact_details": [],
                        "death_date": "",
                        "email": None,
                        "extra_fields": [{"favourite_biscuits": ""}],
                        "gender": "",
                        "honorific_prefix": "",
                        "honorific_suffix": "",
                        "id": 2009,
                        "identifiers": [],
                        "images": [],
                        "links": [],
                        "memberships": [
                            {
                                "elected": None,
                                "election": {
                                    "id": "gla.a.2016-05-05",
                                    "name": "2016 London Assembly Election (Additional)",
                                    "url": "http://testserver/api/v0.9/elections/gla.a.2016-05-05/",
                                },
                                "end_date": None,
                                "id": membership_pk,
                                "label": "",
                                "on_behalf_of": {
                                    "id": "party:53",
                                    "name": "Labour Party",
                                },
                                "party_list_position": None,
                                "person": {
                                    "id": 2009,
                                    "name": "Tessa Jowell",
                                    "url": "http://testserver/api/v0.9/persons/2009/",
                                },
                                "post": {
                                    "id": "london",
                                    "label": "Assembly Member",
                                    "slug": "london",
                                    "url": "http://testserver/api/v0.9/posts/london/",
                                },
                                "role": "Candidate",
                                "start_date": None,
                                "url": "http://testserver/api/v0.9/memberships/{}/".format(
                                    membership_pk
                                ),
                            }
                        ],
                        "name": "Tessa Jowell",
                        "other_names": [],
                        "sort_name": "",
                        "thumbnail": None,
                        "url": "http://testserver/api/v0.9/persons/2009/",
                    }
                ],
                "election_date": text_type(self.future_date.isoformat()),
                "election_id": "gla.a.2016-05-05",
                "election_name": "2016 London Assembly Election (Additional)",
                "organization": "London Assembly",
                "post": {
                    "post_candidates": None,
                    "post_name": "Assembly Member",
                    "post_slug": "london",
                },
            },
        ]

        self.assertEqual(expected, output)


class TestCurrentElections(UK2015ExamplesMixin, WebTest):
    def test_future_flag(self):
        # Make the earlier election current
        self.earlier_election.current = True
        self.earlier_election.save()
        req = self.app.get("/api/current-elections/")
        self.assertSetEqual(
            set(req.json.keys()),
            {
                "parl.2015-05-07",
                "parl.2010-05-06",
                "local.maidstone.2016-05-05",
            },
        )

        req = self.app.get("/api/current-elections/?future=1")
        self.assertSetEqual(set(req.json.keys()), {"parl.2015-05-07"})
