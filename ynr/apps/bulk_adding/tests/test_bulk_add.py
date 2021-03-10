from django_webtest import WebTest

from bulk_adding.models import RawPeople
from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import MembershipFactory
from candidates.tests.test_update_view import membership_id_set
from candidates.tests.uk_examples import UK2015ExamplesMixin
from official_documents.models import OfficialDocument
from parties.tests.factories import PartyDescriptionFactory
from people.models import Person
from people.tests.factories import PersonFactory
from popolo.models import Membership
from utils.testing_utils import FuzzyInt


class TestBulkAdding(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def testNoFormIfNoSopn(self):
        response = self.app.get(
            "/bulk_adding/sopn/parl.65808.2015-05-07/",
            user=self.user_who_can_upload_documents,
        )

        self.assertContains(
            response, "This post doesn't have a nomination paper"
        )

        self.assertNotContains(response, "Review")

    def testFormIfSopn(self):
        post = self.dulwich_post

        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.dulwich_post_ballot,
            uploaded_file="sopn.pdf",
        )

        response = self.app.get(
            "/bulk_adding/sopn/parl.65808.2015-05-07/",
            user=self.user_who_can_upload_documents,
        )

        self.assertNotContains(
            response, "This post doesn't have a nomination paper"
        )

        self.assertContains(response, "Review")

    def test_submitting_form(self):
        post = self.dulwich_post

        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.dulwich_post_ballot,
            uploaded_file="sopn.pdf",
        )
        # Add a party description
        party_description = PartyDescriptionFactory(
            description="Green Party Stop Fracking Now", party=self.green_party
        )

        response = self.app.get(
            "/bulk_adding/sopn/parl.65808.2015-05-07/", user=self.user
        )

        form = response.forms["bulk_add_form"]
        form["form-0-name"] = "Homer Simpson"
        party_id = f"{self.green_party.ec_id}__{party_description.pk}"
        form["form-0-party"] = party_id

        response = form.submit()
        self.assertEqual(response.status_code, 302)

        # This takes us to a page with a radio button for adding them
        # as a new person or alternative radio buttons if any
        # candidates with similar names were found.
        response = response.follow()
        form = response.forms[1]
        form["form-0-select_person"].select("_new")

        # As Chris points out[1], this is quite a large number, and also quite
        # arbitrary.
        #
        # The reason for the large number is explained in the GitHub thread
        # linked to below. The arbitrariness isn't amazing, but the idea is to
        # make it lower and at least make sure it's not getting bigger.
        #
        # [1]: https://github.com/DemocracyClub/yournextrepresentative/pull/467#discussion_r179186705
        with self.assertNumQueries(FuzzyInt(54, 58)):
            response = form.submit()

        self.assertEqual(Person.objects.count(), 1)
        homer = Person.objects.get()
        self.assertEqual(homer.name, "Homer Simpson")
        homer_versions = homer.versions
        self.assertEqual(len(homer_versions), 2)
        self.assertEqual(
            homer_versions[0]["information_source"], "http://example.com"
        )
        self.assertEqual(
            homer_versions[1]["information_source"], "http://example.com"
        )

        self.assertEqual(homer.memberships.count(), 1)
        membership = homer.memberships.get()
        self.assertEqual(membership.role, "Candidate")
        self.assertEqual(membership.party.name, "Green Party")
        self.assertEqual(
            membership.post.label,
            "Member of Parliament for Dulwich and West Norwood",
        )
        self.assertEqual(membership.party_name, "Green Party")
        self.assertEqual(membership.party_description, party_description)
        self.assertEqual(
            membership.party_description_text, "Green Party Stop Fracking Now"
        )

    def _run_wizard_to_end(self):
        existing_person = PersonFactory.create(
            id="1234567", name="Bart Simpson"
        )
        existing_membership = MembershipFactory.create(
            person=existing_person,
            post=self.local_post,
            party=self.labour_party,
            ballot=self.local_election.ballot_set.get(post=self.local_post),
        )
        memberships_before = membership_id_set(existing_person)
        # Now try adding that person via bulk add:
        response = self.app.get(
            "/bulk_adding/sopn/parl.65808.2015-05-07/?edit=1", user=self.user
        )

        form = response.forms["bulk_add_form"]
        form["form-0-name"] = "Bart Simpson"
        form["form-0-party"] = self.green_party.ec_id

        response = form.submit()
        self.assertEqual(RawPeople.objects.count(), 1)
        self.assertEqual(
            RawPeople.objects.get().source_type, RawPeople.SOURCE_BULK_ADD_FORM
        )
        self.assertEqual(response.status_code, 302)
        # This takes us to a page with a radio button for adding them
        # as a new person or alternative radio buttons if any
        # candidates with similar names were found.
        response = response.follow()
        form = response.forms[1]
        form["form-0-select_person"].select("1234567")
        response = form.submit()

        self.assertFalse(RawPeople.objects.exists())
        person = Person.objects.get(name="Bart Simpson")
        memberships_after = membership_id_set(person)
        new_memberships = memberships_after - memberships_before
        self.assertEqual(len(new_memberships), 1)
        new_membership = Membership.objects.get(pk=list(new_memberships)[0])
        self.assertEqual(new_membership.post, self.dulwich_post)
        self.assertEqual(new_membership.party, self.green_party)
        same_memberships = memberships_before & memberships_after
        self.assertEqual(len(same_memberships), 1)
        same_membership = Membership.objects.get(pk=list(same_memberships)[0])
        self.assertEqual(same_membership.post, self.local_post)
        self.assertEqual(same_membership.party, self.labour_party)
        self.assertEqual(same_membership.id, existing_membership.id)

        return response

    def test_adding_to_existing_person(self):
        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.dulwich_post_ballot,
            uploaded_file="sopn.pdf",
        )
        response = self._run_wizard_to_end()
        # We expect to go to the ballot page
        self.assertEqual(
            response.location, self.dulwich_post_ballot.get_absolute_url()
        )
        new_response = response.follow()
        self.assertFalse(RawPeople.objects.exists())
        # Test the flash message
        self.assertContains(
            new_response, "There are still more documents that verifying!"
        )

    def test_flash_message_with_doc_for_multiple_ballots(self):
        # Make a new document
        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.dulwich_post_ballot,
            uploaded_file="sopn.pdf",
        )
        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.camberwell_post_ballot,
            uploaded_file="sopn.pdf",
        )
        response = self._run_wizard_to_end()
        # We expect to get directed to the "documents for post" page
        self.assertTrue(
            response.location.startswith("/upload_document/posts_for_document/")
        )
        new_response = response.follow()
        # Test the flash message
        self.assertContains(new_response, "…and while you're here…")

    def test_adding_to_existing_person_same_election(self):
        # This could happen if someone's missed that there was the
        # same person already listed on the first page, but then
        # spotted them on the review page and said to merge them then.
        existing_person = PersonFactory.create(
            id="1234567", name="Bart Simpson"
        )
        existing_membership = MembershipFactory.create(
            person=existing_person,
            # !!! This is the line that differs from the previous test:
            post=self.dulwich_post,
            party=self.labour_party,
            ballot=self.election.ballot_set.get(post=self.dulwich_post),
        )
        memberships_before = membership_id_set(existing_person)
        # Now try adding that person via bulk add:
        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.dulwich_post_ballot,
            uploaded_file="sopn.pdf",
        )

        response = self.app.get(
            "/bulk_adding/sopn/parl.65808.2015-05-07/", user=self.user
        )

        form = response.forms["bulk_add_form"]
        form["form-0-name"] = "Bart Simpson"
        form["form-0-party"] = self.green_party.ec_id

        response = form.submit()
        self.assertEqual(response.status_code, 302)

        # This takes us to a page with a radio button for adding them
        # as a new person or alternative radio buttons if any
        # candidates with similar names were found.
        response = response.follow()
        form = response.forms[1]
        form["form-0-select_person"].select("1234567")
        response = form.submit()

        person = Person.objects.get(name="Bart Simpson")
        memberships_after = membership_id_set(person)
        new_memberships = memberships_after - memberships_before
        self.assertEqual(len(new_memberships), 0)
        same_memberships = memberships_before & memberships_after
        self.assertEqual(len(same_memberships), 1)
        same_membership = Membership.objects.get(pk=list(same_memberships)[0])
        self.assertEqual(same_membership.post, self.dulwich_post)
        self.assertEqual(same_membership.party, self.green_party)
        self.assertEqual(same_membership.id, existing_membership.id)

    def test_old_url_redirects(self):
        response = self.app.get(
            "/bulk_adding/parl.2015-05-07/65808/", user=self.user
        )

        self.assertEqual(response.status_code, 302)

    def test_redirect_to_review_form(self):
        RawPeople.objects.create(
            ballot=self.dulwich_post_ballot,
            data=[{"name": "Bart", "party_id": "PP52"}],
        )
        response = self.app.get(
            "/bulk_adding/sopn/parl.65808.2015-05-07/", user=self.user
        )
        self.assertEqual(response.status_code, 302)
        response.forms

        response = self.app.get(
            "/bulk_adding/sopn/parl.65808.2015-05-07/?edit=1", user=self.user
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_with_no_memberships_or_raw_people(self):
        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.dulwich_post_ballot,
            uploaded_file="sopn.pdf",
        )
        response = self.app.get(
            "/bulk_adding/sopn/parl.65808.2015-05-07/?edit=1", user=self.user
        )
        form = response.forms[1]
        response = form.submit()
        self.assertContains(
            response, "At least one person required on this ballot"
        )

    def test_valid_with_memberships_and_no_raw_people(self):
        existing_person = PersonFactory.create(
            id="1234567", name="Bart Simpson"
        )
        existing_membership = MembershipFactory.create(
            person=existing_person,
            # !!! This is the line that differs from the previous test:
            post=self.dulwich_post,
            party=self.labour_party,
            ballot=self.election.ballot_set.get(post=self.dulwich_post),
        )

        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.dulwich_post_ballot,
            uploaded_file="sopn.pdf",
        )
        response = self.app.get(
            "/bulk_adding/sopn/parl.65808.2015-05-07/?edit=1", user=self.user
        )
        form = response.forms[1]
        response = form.submit()
        self.assertEqual(response.status_code, 302)

    def test_remove_other_ballots_in_election(self):
        """
        If someone is adding this person to a ballot, we remove that person from
        other ballots in that election
        """
        existing_person = PersonFactory.create(
            id="1234567", name="Bart Simpson"
        )

        existing_membership = MembershipFactory.create(
            person=existing_person,
            # !!! This is the line that differs from the previous test:
            post=self.dulwich_post,
            party=self.labour_party,
            ballot=self.election.ballot_set.get(post=self.dulwich_post),
        )

        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.camberwell_post_ballot,
            uploaded_file="sopn.pdf",
        )

        response = self.app.get(
            "/bulk_adding/sopn/parl.{}.2015-05-07/".format(
                self.camberwell_post.slug
            ),
            user=self.user,
        )

        form = response.forms["bulk_add_form"]
        form["form-0-name"] = "Bart Simpson"
        form["form-0-party"] = self.green_party.ec_id

        response = form.submit()

        response = response.follow()
        form = response.forms[1]
        form["form-0-select_person"].select("1234567")
        response = form.submit()
        self.assertEqual(response.context["formset"].is_valid(), False)
        self.assertEqual(
            response.context["formset"].non_form_errors(),
            [
                "'Bart Simpson' is marked as standing in another ballot for "
                "this election. Check you're entering the correct information "
                "for Member of Parliament for Camberwell and Peckham"
            ],
        )
        self.assertContains(
            response, "is marked as standing in another ballot for"
        )
