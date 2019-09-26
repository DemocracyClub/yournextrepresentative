import re

from django.conf import settings
from django.utils.six.moves.urllib_parse import urljoin, urlsplit
from django_webtest import WebTest
from mock import Mock, patch

from candidates.tests.factories import (
    ElectionFactory,
    ParliamentaryChamberFactory,
    PartySetFactory,
    PostFactory,
)

from .ee_postcode_results import ee_se240ag_result, ee_sw1a1aa_result


def fake_requests_for_every_election(url, *args, **kwargs):
    """Return reduced EE output for some known URLs"""

    EE_BASE_URL = getattr(
        settings, "EE_BASE_URL", "https://elections.democracyclub.org.uk/"
    )

    if url == urljoin(EE_BASE_URL, "/api/elections/?postcode=se240ag"):
        status_code = 200
        json_result = ee_se240ag_result
    elif url == urljoin(EE_BASE_URL, "/api/elections/?postcode=se240xx"):
        status_code = 400
        json_result = {"detail": "Unknown postcode"}
    elif url == urljoin(EE_BASE_URL, "/api/elections/?coords=-0.143207%2C51.5"):
        status_code = 200
        json_result = ee_se240ag_result
    elif url == urljoin(EE_BASE_URL, "/api/elections/?postcode=sw1a1aa"):
        status_code = 200
        json_result = ee_sw1a1aa_result
    elif url == urljoin(EE_BASE_URL, "/api/elections/?postcode=cb28rq"):
        status_code = 404
        json_result = {
            "code": 404,
            "error": 'The url "{}" couldn’t be found'.format(url),
        }
    else:
        raise Exception("URL that hasn't been mocked yet: " + url)
    return Mock(
        **{"json.return_value": json_result, "status_code": status_code}
    )


@patch("elections.uk.geo_helpers.requests")
class TestHomePageView(WebTest):
    def setUp(self):
        gb_parties = PartySetFactory.create(slug="gb", name="Great Britain")
        commons = ParliamentaryChamberFactory.create()
        election = ElectionFactory.create(
            slug="parl.2017-03-23",
            name="2015 General Election",
            organization=commons,
            election_date="2017-03-23",
        )
        PostFactory.create(
            elections=(election,),
            organization=commons,
            slug="dulwich-and-west-norwood",
            label="Member of Parliament for Dulwich and West Norwood",
            party_set=gb_parties,
        )

    def _setup_extra_posts(self):
        # Create some extra posts and areas:
        london_assembly = ParliamentaryChamberFactory.create(
            slug="london-assembly", name="London Assembly"
        )
        election_lac = ElectionFactory.create(
            slug="gla.c.2016-05-05",
            organization=london_assembly,
            name="2016 London Assembly Election (Constituencies)",
        )
        election_gla = ElectionFactory.create(
            slug="gla.a.2016-05-05",
            organization=london_assembly,
            name="2016 London Assembly Election (Additional)",
        )
        PostFactory.create(
            elections=(election_lac,),
            organization=london_assembly,
            slug="lambeth-and-southwark",
            label="Assembly Member for Lambeth and Southwark",
        )
        PostFactory.create(
            elections=(election_gla,),
            organization=london_assembly,
            slug="london",
            label="2016 London Assembly Election (Additional)",
        )

    def test_front_page(self, mock_requests):
        response = self.app.get("/")
        # Check that there is a form on that page
        response.forms["form-postcode"]

    def test_valid_postcode_redirects_to_constituency(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_every_election
        response = self.app.get("/")
        form = response.forms["form-postcode"]
        form["q"] = "SE24 0AG"
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual(split_location.path, "/")
        self.assertEqual(split_location.query, "q=SE24%200AG")
        response = self.app.get(response.location)
        split_location = urlsplit(response.location)
        self.assertEqual(split_location.path, "/postcode/SE24%200AG/")
        # follow the redirect
        response = response.follow()
        self.assertEqual(len(response.context["ballots"]), 1)
        self.assertContains(response, "2015 General Election")

    def test_invalid_postcode(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_every_election
        response = self.app.get("/")
        form = response.forms["form-postcode"]
        form["q"] = "SE24 0XX"
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        response = self.app.get(response.location)

        self.assertEqual(
            response.context["postcode_form"].errors,
            {"q": ["The postcode \u201cSE24 0XX\u201d couldn\u2019t be found"]},
        )

    def test_valid_postcode_returns_multiple_areas(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_every_election

        self._setup_extra_posts()

        response = self.app.get("/")
        form = response.forms["form-postcode"]
        form["q"] = "SE24 0AG"
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual(split_location.path, "/")
        self.assertEqual(split_location.query, "q=SE24%200AG")
        response = self.app.get(response.location)
        split_location = urlsplit(response.location)
        self.assertEqual(split_location.path, "/postcode/SE24%200AG/")
        response = response.follow()
        self.assertEqual(len(response.context["ballots"]), 3)
        self.assertContains(
            response, "2016 London Assembly Election (Additional)"
        )
        self.assertContains(
            response, "2016 London Assembly Election (Constituencies)"
        )
        self.assertContains(response, "2015 General Election")

    def test_unknown_postcode_returns_to_finder_with_error(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_every_election
        response = self.app.get("/")
        form = response.forms["form-postcode"]
        # This looks like a postcode to the usual postcode-checking
        # regular expressions, but doesn't actually exist
        form["q"] = "CB2 8RQ"
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual(split_location.path, "/")
        self.assertEqual(split_location.query, "q=CB2%208RQ")
        response = self.app.get(response.location)
        self.assertIn("The postcode “CB2 8RQ” couldn’t be found", response)

    def test_nonsense_postcode_searches_for_candidate(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_every_election
        response = self.app.get("/")
        form = response.forms["form-postcode"]
        # This looks like a postcode to the usual postcode-checking
        # regular expressions, but doesn't actually exist
        form["q"] = "foo bar"
        response = form.submit()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Search candidates", response)
        a = response.html.find(
            "a", text=re.compile('Add "foo bar" as a new candidate')
        )
        self.assertEqual(
            a["href"], "/person/create/select_election?name=foo bar"
        )

    def test_nonascii_postcode(self, mock_requests):
        # This used to produce a particular error, but now goes to the
        # search candidates page. Assert the new behaviour:
        mock_requests.get.side_effect = fake_requests_for_every_election
        response = self.app.get("/")
        form = response.forms["form-postcode"]
        # Postcodes with non-ASCII characters aren't postcodes, so
        # it'll assume this is a search for a person.
        form["q"] = "SW1A 1ӔA"
        response = form.submit()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Search candidates", response)
        a = response.html.find(
            "a", text=re.compile('Add "SW1A 1ӔA" as a new candidate')
        )
        self.assertEqual(
            a["href"], "/person/create/select_election?name=SW1A 1\u04d4A"
        )

    def test_valid_coords_redirects_to_constituency(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_every_election
        response = self.app.get("/geolocator/-0.143207,51.5")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["ballots"]), 1)

    def test_valid_coords_redirects_with_multiple_elections(
        self, mock_requests
    ):
        mock_requests.get.side_effect = fake_requests_for_every_election
        self._setup_extra_posts()
        response = self.app.get("/geolocator/-0.143207,51.5")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["ballots"]), 3)
