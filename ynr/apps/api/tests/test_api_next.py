from datetime import date, timedelta

from django.core.files.storage import DefaultStorage
from django_webtest import WebTest
from mock import patch

from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import (
    ElectionFactory,
    MembershipFactory,
    ParliamentaryChamberFactory,
    PostFactory,
)
from candidates.tests.helpers import TmpMediaRootMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME
from official_documents.models import OfficialDocument
from parties.tests.factories import PartyDescriptionFactory, PartyEmblemFactory
from people.models import PersonImage
from people.tests.factories import PersonFactory

from .test_upcoming_elections_api import fake_requests_for_every_election


class TestAPI(TmpMediaRootMixin, TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        self.storage = DefaultStorage()

        self.person = PersonFactory.create(id=2009, name="Tessa Jowell")
        self.person_image = PersonImage.objects.update_or_create_from_file(
            EXAMPLE_IMAGE_FILENAME,
            "images/imported.jpg",
            self.person,
            defaults={
                "md5sum": "md5sum",
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "Here's an image...",
                "is_primary": True,
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
        MembershipFactory.create(
            person=self.person, ballot=self.edinburgh_east_post_ballot
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

        self.assertEqual(json["persons"], "http://testserver/api/next/persons/")
        self.assertEqual(
            json["organizations"], "http://testserver/api/next/organizations/"
        )
        self.assertEqual(
            json["elections"], "http://testserver/api/next/elections/"
        )
        self.assertEqual(json["posts"], "http://testserver/api/next/posts/")

        persons_resp = self.app.get("/api/next/persons/")
        self.assertEqual(persons_resp.status_code, 200)

        organizations_resp = self.app.get("/api/next/organizations/")
        self.assertEqual(organizations_resp.status_code, 200)

        elections_resp = self.app.get("/api/next/elections/")
        self.assertEqual(elections_resp.status_code, 200)

        posts_resp = self.app.get("/api/next/posts/")
        self.assertEqual(posts_resp.status_code, 200)

        parties_resp = self.app.get("/api/next/parties/")
        self.assertEqual(parties_resp.status_code, 200)

    def test_party_endpoint(self):
        parties_resp = self.app.get("/api/next/parties/")
        self.assertEqual(parties_resp.json["count"], 7)

    def test_person_endpoint_smoke_test(self):
        response = self.app.get("/api/next/persons/")
        result_json = response.json
        self.assertEqual(result_json["count"], 5)

        response = self.app.get("/api/next/persons/2009/")
        result_json = response.json
        self.assertTrue(result_json["images"][0]["is_primary"])

    def test_all_parties_view(self):
        # Test with no register
        response = self.app.get("/all-parties.json", expect_errors=True)
        self.assertEqual(response.status_code, 400)

        # Test with GB register
        response = self.app.get("/all-parties.json?register=GB")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {
                "items": [
                    {"id": "", "text": ""},
                    {"id": "PP52", "text": "Conservative Party"},
                    {"id": "PP63", "text": "Green Party"},
                    {"id": "ynmp-party:2", "text": "Independent"},
                    {
                        "children": [
                            {"id": "PP53", "text": "Labour Party"},
                            {"id": "PP53__1", "text": "Labour Party Candidate"},
                        ],
                        "text": "Labour Party",
                    },
                    {"id": "PP90", "text": "Liberal Democrats"},
                    {
                        "id": "ynmp-party:12522",
                        "text": "Speaker seeking re-election",
                    },
                ]
            },
        )

        # Test with NI register
        response = self.app.get("/all-parties.json?register=NI")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {
                "items": [
                    {"id": "", "text": ""},
                    {"id": "ynmp-party:2", "text": "Independent"},
                    {"id": "PP39", "text": "Sinn Féin"},
                    {
                        "id": "ynmp-party:12522",
                        "text": "Speaker seeking re-election",
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
            "/api/next/post_elections/{}/".format(self.dulwich_post_ballot.pk)
        )
        result = response.json
        self.assertEqual(
            result["sopn"],
            {
                "document_type": "Nomination paper",
                "uploaded_file": None,
                "ballot": "http://testserver/api/next/post_elections/{}/".format(
                    self.dulwich_post_ballot.pk
                ),
                "source_url": "",
            },
        )
