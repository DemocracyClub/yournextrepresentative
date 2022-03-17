from django.core.files.storage import DefaultStorage
from django_webtest import WebTest

from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import MembershipFactory
from candidates.tests.helpers import TmpMediaRootMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME
from official_documents.models import OfficialDocument
from parties.models import Party
from parties.tests.factories import PartyDescriptionFactory, PartyEmblemFactory
from parties.tests.fixtures import DefaultPartyFixtures
from people.models import PersonImage
from people.tests.factories import PersonFactory


class TestAPI(
    DefaultPartyFixtures,
    TmpMediaRootMixin,
    TestUserMixin,
    UK2015ExamplesMixin,
    WebTest,
):
    def setUp(self):
        super().setUp()
        self.storage = DefaultStorage()

        self.person = PersonFactory.create(id=2009, name="Tessa Jowell")
        self.person_image = PersonImage.objects.create_from_file(
            filename=EXAMPLE_IMAGE_FILENAME,
            new_filename="images/imported.jpg",
            defaults={
                "person": self.person,
                "md5sum": "md5sum",
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "Here's an image...",
                "source": "Found on the candidate's Flickr feed",
            },
        )

        dulwich_not_stand = PersonFactory.create(id=4322, name="Helen Hayes")
        edinburgh_candidate = PersonFactory.create(
            id="818", name="Sheila Gilmore"
        )
        edinburgh_winner = PersonFactory.create(
            id="5795", name="Tommy Sheppard"
        )
        edinburgh_may_stand = PersonFactory.create(
            id="5163", name="Peter McColl"
        )
        MembershipFactory.create(
            person=self.person,
            post=self.dulwich_post,
            party=self.labour_party,
            ballot=self.dulwich_post_ballot,
        )
        self.independent_party_object = Party.objects.get(ec_id="ynmp-party:2")
        MembershipFactory.create(
            person=self.person,
            ballot=self.edinburgh_east_post_ballot,
            party=self.independent_party_object,
        )

        MembershipFactory.create(
            person=dulwich_not_stand,
            post=self.dulwich_post,
            party=self.labour_party,
            ballot=self.dulwich_post_ballot_earlier,
        )
        dulwich_not_stand.not_standing.add(self.election)

        MembershipFactory.create(
            person=edinburgh_winner,
            post=self.edinburgh_east_post,
            party=self.labour_party,
            elected=True,
            ballot=self.edinburgh_east_post_ballot,
        )

        MembershipFactory.create(
            person=edinburgh_candidate,
            post=self.edinburgh_east_post,
            party=self.labour_party,
            ballot=self.edinburgh_east_post_ballot,
        )

        MembershipFactory.create(
            person=edinburgh_may_stand,
            post=self.edinburgh_east_post,
            party=self.labour_party,
            ballot=self.edinburgh_east_post_ballot_earlier,
        )

        PartyEmblemFactory(party=self.labour_party)
        PartyDescriptionFactory(
            party=self.labour_party, description="Labour Party Candidate", pk=1
        )

    def test_api_basic_response(self):
        response = self.app.get("/api/next/")
        self.assertEqual(response.status_code, 200)
        json = response.json

        self.assertEqual(json["people"], "http://testserver/api/next/people/")
        self.assertEqual(
            json["organizations"], "http://testserver/api/next/organizations/"
        )
        self.assertEqual(
            json["elections"], "http://testserver/api/next/elections/"
        )

        people_resp = self.app.get("/api/next/people/")
        self.assertEqual(people_resp.status_code, 200)

        organizations_resp = self.app.get("/api/next/organizations/")
        self.assertEqual(organizations_resp.status_code, 200)

        elections_resp = self.app.get("/api/next/elections/")
        self.assertEqual(elections_resp.status_code, 200)

        parties_resp = self.app.get("/api/next/parties/")
        self.assertEqual(parties_resp.status_code, 200)

    def test_party_endpoint(self):
        parties_resp = self.app.get("/api/next/parties/")
        self.assertEqual(parties_resp.json["count"], 7)

    def test_party_csv_endpoint(self):
        parties_resp = self.app.get("/api/next/current_parties_csv/")
        self.assertEqual(
            parties_resp.text,
            (
                "name,ec_id,current_candidates\r\n"
                "Labour Party,53,1\r\n"
                "Liberal Democrats,90,1\r\n"
                "Green Party,63,1\r\n"
                "Conservative Party,52,1\r\n"
                "Speaker seeking re-election,ynmp-party:12522,0\r\n"
                "Independent,ynmp-party:2,0\r\n"
            ),
        )

        parties_resp = self.app.get(
            "/api/next/current_parties_csv/?register=NI"
        )
        self.assertEqual(
            parties_resp.text,
            (
                "name,ec_id,current_candidates\r\n"
                "Sinn Féin,39,1\r\n"
                "Speaker seeking re-election,ynmp-party:12522,0\r\n"
                "Independent,ynmp-party:2,0\r\n"
            ),
        )

    def test_person_endpoint_smoke_test(self):
        response = self.app.get("/api/next/people/")
        result_json = response.json
        self.assertEqual(result_json["count"], 5)

        response = self.app.get("/api/next/people/2009/")
        result_json = response.json
        self.assertTrue(result_json["image"])
        self.assertEqual(
            result_json["candidacies"][0]["previous_party_affiliations"], []
        )

    def test_all_parties_view(self):
        self.maxDiff = None
        # Test with GB register
        response = self.app.get("/all-parties.json?register=GB")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {
                "items": [
                    {"id": "", "text": "", "register": "all"},
                    {
                        "id": "PP52",
                        "text": "Conservative Party",
                        "register": "GB",
                    },
                    {"id": "PP63", "text": "Green Party", "register": "GB"},
                    {
                        "children": [
                            {
                                "id": "ynmp-party:2",
                                "register": "all",
                                "text": "Independent",
                            },
                            {
                                "id": "ynmp-party:2__1000",
                                "register": "all",
                                "text": "[blank]",
                            },
                            {
                                "id": "ynmp-party:2__1001",
                                "register": "all",
                                "text": "[No party listed]",
                            },
                        ],
                        "text": "Independent",
                    },
                    {
                        "children": [
                            {
                                "id": "PP53",
                                "text": "Labour Party",
                                "register": "GB",
                            },
                            {
                                "id": "PP53__1",
                                "text": "Labour Party " "Candidate",
                                "register": "GB",
                            },
                        ],
                        "text": "Labour Party",
                    },
                    {
                        "id": "PP90",
                        "text": "Liberal Democrats",
                        "register": "GB",
                    },
                    {
                        "id": "ynmp-party:12522",
                        "text": "Speaker seeking re-election",
                        "register": "all",
                    },
                ]
            },
            response.json,
        )

        # Test with NI register
        response = self.app.get("/all-parties.json?register=NI")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {
                "items": [
                    {"id": "", "text": "", "register": "all"},
                    {
                        "children": [
                            {
                                "id": "ynmp-party:2",
                                "register": "all",
                                "text": "Independent",
                            },
                            {
                                "id": "ynmp-party:2__1000",
                                "register": "all",
                                "text": "[blank]",
                            },
                            {
                                "id": "ynmp-party:2__1001",
                                "register": "all",
                                "text": "[No party listed]",
                            },
                        ],
                        "text": "Independent",
                    },
                    {"id": "PP39", "text": "Sinn Féin", "register": "NI"},
                    {
                        "id": "ynmp-party:12522",
                        "text": "Speaker seeking re-election",
                        "register": "all",
                    },
                ]
            },
        )

    def test_sopn_on_ballot(self):
        OfficialDocument.objects.create(
            ballot=self.dulwich_post_ballot,
            document_type=OfficialDocument.NOMINATION_PAPER,
        )
        response = self.app.get(
            "/api/next/ballots/{}/".format(
                self.dulwich_post_ballot.ballot_paper_id
            )
        )
        result = response.json
        self.assertEqual(
            result["sopn"],
            {
                "document_type": "Nomination paper",
                "uploaded_file": None,
                "source_url": "",
            },
        )
