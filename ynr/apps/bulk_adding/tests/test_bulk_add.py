from unittest.mock import patch

from bulk_adding.forms import BulkAddFormSet
from bulk_adding.models import RawPeople
from candidates.models.db import ActionType, EditType, LoggedAction
from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import MembershipFactory
from candidates.tests.test_update_view import membership_id_set
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django_webtest import WebTest
from official_documents.models import OfficialDocument
from parties.models import Party
from parties.tests.factories import PartyDescriptionFactory, PartyFactory
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

    def test_with_raw_people_regression_test(self):
        """
        Simple test to check that the page renders when a RawPeople object
        exists for the ballot. This is a regression test, as previously the
        BulkAddFormSet would initialise with party data returned as a string
        but now expects a list or tuple.
        """
        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.dulwich_post_ballot,
            uploaded_file="sopn.pdf",
        )
        RawPeople.objects.create(
            ballot=self.dulwich_post_ballot,
            data=[{"name": "Bart", "party_id": "PP52"}],
            source_type=RawPeople.SOURCE_PARSED_PDF,
        )
        response = self.app.get(
            "/bulk_adding/sopn/parl.65808.2015-05-07/", user=self.user
        )
        self.assertEqual(response.status_code, 200)

    def test_with_party_not_from_default_choices(self):
        """
        Regression test to check that when a Party is selected that was not
        included in the initially loaded parties from the default_party_choices
        method, that the review step validates and passes. Previously this was
        causing a 500 error see:
        https://sentry.io/organizations/democracy-club-gp/issues/2326522296/?project=169287&query=is%3Aunresolved
        """
        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.dulwich_post_ballot,
            uploaded_file="sopn.pdf",
        )
        # create a party that isnt included in the default_party_choices as it
        # doesnt have any current candidates
        barnsley_independents = PartyFactory(
            ec_id="PP530",
            name="Barnsley Independent Group",
            legacy_slug="party:530",
            register="GB",
            current_candidates=0,
        )
        response = self.app.get(
            "/bulk_adding/sopn/parl.65808.2015-05-07/", user=self.user
        )
        form = response.forms["bulk_add_form"]
        form["form-0-name"] = "Homer Simpson"
        # get ec_ids from PartySelectField choices that were initially loaded
        party_choices_ec_ids = [
            choice[0] for choice in form["form-0-party_0"].options
        ]
        self.assertNotIn(barnsley_independents.ec_id, party_choices_ec_ids)
        # set value to party that wasnt loaded initially - mimicking the
        # "load more parties" flow
        form["form-0-party_1"] = barnsley_independents.ec_id
        # submit the form to proceed to review step
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        response = response.follow()
        #  confirm as a new person and submit lock suggestion
        form = response.forms["bulk_add_review_formset"]
        form["form-0-select_person"].select("_new")
        response = form.submit().follow()
        # previously this raised a 500 error caused by
        # AttributeError: 'ReviewSinglePersonFormFormSet' object has no
        # attribute 'cleaned_data'
        self.assertEqual(response.status_code, 200)

    def test_submitting_form(self):
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

        with self.assertNumQueries(21):
            response = self.app.get(
                "/bulk_adding/sopn/parl.65808.2015-05-07/", user=self.user
            )

        form = response.forms["bulk_add_form"]
        form["form-0-name"] = "Homer Simpson"
        party_id = f"{self.green_party.ec_id}__{party_description.pk}"
        form["form-0-party_1"] = party_id

        response = form.submit()
        self.assertEqual(response.status_code, 302)

        # This takes us to a page with a radio button for adding them
        # as a new person or alternative radio buttons if any
        # candidates with similar names were found.
        response = response.follow()
        form = response.forms["bulk_add_review_formset"]
        form["form-0-select_person"].select("_new")

        # As Chris points out[1], this is quite a large number, and also quite
        # arbitrary.
        #
        # The reason for the large number is explained in the GitHub thread
        # linked to below. The arbitrariness isn't amazing, but the idea is to
        # make it lower and at least make sure it's not getting bigger.
        #
        # [1]: https://github.com/DemocracyClub/yournextrepresentative/pull/467#discussion_r179186705
        with self.assertNumQueries(FuzzyInt(53, 55)):
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

    def test_submitting_form_when_candidates_locked(self):
        """
        Tests that if candidates have been locked whilst another user
        is completing the bulk add process to create a lock suggestion
        that the lock suggestion is not created
        """
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
        form["form-0-party_1"] = party_id

        response = form.submit()
        self.assertEqual(response.status_code, 302)

        # meanwhile candidates have been locked
        self.dulwich_post_ballot.candidates_locked = True
        self.dulwich_post_ballot.save()

        response = response.follow()
        form = response.forms["bulk_add_review_formset"]
        form["form-0-select_person"].select("_new")
        response = form.submit()
        self.assertEqual(
            self.dulwich_post_ballot.suggestedpostlock_set.count(), 0
        )
        self.assertContains(
            response, "Candidates have already been locked for this ballot"
        )

    def test_submitting_form_with_previous_party_affiliations(self):
        """
        Test that submitting previous party affiliations is possible with a
        welsh ballot, and results in a membership being created with the
        previous_party_affiliations relationships created
        """
        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.senedd_ballot,
            uploaded_file="sopn.pdf",
        )
        with self.assertNumQueries(22):
            response = self.app.get(
                f"/bulk_adding/sopn/{self.senedd_ballot.ballot_paper_id}/",
                user=self.user,
            )

        form = response.forms["bulk_add_form"]
        form["form-0-name"] = "Joe Bloggs"
        party_id = self.ld_party.ec_id
        form["form-0-party_1"] = party_id
        form["form-0-previous_party_affiliations"].select_multiple(
            texts=[self.conservative_party.name, self.labour_party.name]
        )

        response = form.submit()
        self.assertEqual(response.status_code, 302)

        # This takes us to a page with a radio button for adding them
        # as a new person or alternative radio buttons if any
        # candidates with similar names were found.
        response = response.follow()
        form = response.forms["bulk_add_review_formset"]
        form["form-0-select_person"].select("_new")

        # this is a smaller increase but may be unavoidable
        with self.assertNumQueries(FuzzyInt(56, 58)):
            response = form.submit()

        self.assertEqual(Person.objects.count(), 1)
        person = Person.objects.get()
        self.assertEqual(person.name, "Joe Bloggs")
        self.assertEqual(person.memberships.count(), 1)
        membership = person.memberships.get()
        self.assertEqual(membership.role, "Candidate")
        self.assertEqual(membership.party.name, self.ld_party.name)
        self.assertEqual(membership.party_name, self.ld_party.name)
        self.assertEqual(
            set(membership.previous_party_affiliations.all()),
            {self.labour_party, self.conservative_party},
        )

    def test_submitting_form_with_previous_party_affiliations_invalid(self):
        """
        Test that submitting previous party affiliations is possible with a
        welsh ballot, and results in a membership being created with the
        previous_party_affiliations relationships created
        """
        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.dulwich_post_ballot,
            uploaded_file="sopn.pdf",
        )
        response = self.app.get(
            f"/bulk_adding/sopn/{self.dulwich_post_ballot.ballot_paper_id}/",
            user=self.user,
        )

        form = response.forms["bulk_add_form"]
        form["form-0-name"] = "Joe Bloggs"
        party_id = self.ld_party.ec_id
        form["form-0-party_1"] = party_id

        with self.assertRaises(AssertionError) as e:
            form["form-0-previous_party_affiliations"]
            self.assertEqual(
                e.message,
                "No field by the name 'form-0-previous_party_affiliations' found",
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
        form["form-0-party_1"] = self.green_party.ec_id
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
        form = response.forms["bulk_add_review_formset"]
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
            new_response, "There are still more documents that need verifying!"
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
        form["form-0-name"] = "Bartholomew Jojo Simpson"
        form["form-0-party_1"] = self.green_party.ec_id

        response = form.submit()
        self.assertEqual(response.status_code, 302)

        # This takes us to a page with a radio button for adding them
        # as a new person or alternative radio buttons if any
        # candidates with similar names were found.
        response = response.follow()
        form = response.forms["bulk_add_review_formset"]
        form["form-0-select_person"].select("1234567")
        response = form.submit()

        person = Person.objects.get(name="Bartholomew Jojo Simpson")
        self.assertEqual(person.other_names.first().name, "Bart Simpson")
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
            "/bulk_adding/parl.65808.2015-05-07/", user=self.user
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
        form = response.forms["bulk_add_form"]
        response = form.submit()
        self.assertContains(
            response, "At least one person required on this ballot"
        )

    def test_invalid_when_no_party_selected(self):
        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.dulwich_post_ballot,
            uploaded_file="sopn.pdf",
        )
        response = self.app.get(
            "/bulk_adding/sopn/parl.65808.2015-05-07/?edit=1", user=self.user
        )

        form = response.forms["bulk_add_form"]
        form["form-0-name"] = "Bart Simpson"

        response = form.submit()
        form = response.context["formset"][0]

        self.assertEqual(response.status_code, 200)
        self.assertIn("party", form.errors)
        self.assertIn("This field is required.", form.errors["party"])
        self.assertContains(response, "This field is required.")

    def test_valid_when_second_form_only_party_changed(self):
        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.dulwich_post_ballot,
            uploaded_file="sopn.pdf",
        )
        response = self.app.get(
            "/bulk_adding/sopn/parl.65808.2015-05-07/?edit=1", user=self.user
        )

        form = response.forms["bulk_add_form"]
        form["form-0-name"] = "Bart Simpson"
        form["form-0-party_1"] = self.green_party.ec_id
        # change party on a second form, but not the name
        form["form-1-party_1"] = self.green_party.ec_id

        response = form.submit()

        self.assertEqual(response.status_code, 302)
        response = response.follow()
        self.assertNotContains(response, "This field is required.")

    def test_valid_with_memberships_and_no_raw_people(self):
        existing_person = PersonFactory.create(
            id="1234567", name="Bart Simpson"
        )
        MembershipFactory.create(
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
        form = response.forms["bulk_add_form"]
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

        MembershipFactory.create(
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
        form["form-0-party_1"] = self.green_party.ec_id

        response = form.submit()

        response = response.follow()
        form = response.forms["bulk_add_review_formset"]
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

    def test_initial_parties_included_in_party_choices(self):
        # create a party that does not appear in default party list
        PartyFactory(
            ec_id="joint-party:53-119",
            name="Labour and Co-operative Party",
            legacy_slug="joint-party:53-119",
            register="GB",
            current_candidates=0,
        )
        raw_people = RawPeople.objects.create(
            ballot=self.dulwich_post_ballot,
            data=[
                {"name": "Bart", "party_id": "PP52"},
                {"name": "List", "party_id": "joint-party:53-119"},
            ],
            source_type=RawPeople.SOURCE_PARSED_PDF,
        )
        kwargs = {"ballot": self.dulwich_post_ballot}
        kwargs.update(raw_people.as_form_kwargs())
        formset = BulkAddFormSet(**kwargs)
        self.assertIn(
            (
                "joint-party:53-119",
                {"label": "Labour and Co-operative Party", "register": "GB"},
            ),
            formset.parties,
        )
        self.assertEqual(
            formset.initial_party_ids, ["PP52", "joint-party:53-119"]
        )

    def test_get_previous_party_affiliations_choices_called_on_init(self):
        kwargs = {"ballot": self.dulwich_post_ballot}
        with patch.object(
            BulkAddFormSet, "get_previous_party_affiliations_choices"
        ) as mock:
            BulkAddFormSet(**kwargs)
            mock.assert_called_once()

    def test_get_previous_party_affiliations_choices(self):
        # check when non-welsh ballot empty list returned
        kwargs = {"ballot": self.dulwich_post_ballot}
        formset = BulkAddFormSet(**kwargs)
        self.assertEqual(formset.get_previous_party_affiliations_choices(), [])

        # check with a welsh ballot party choices returned
        expected = [
            (party.ec_id, party.name) for party in Party.objects.register("GB")
        ]
        kwargs = {"ballot": self.senedd_ballot}
        formset = BulkAddFormSet(**kwargs)
        self.assertEqual(
            set(formset.get_previous_party_affiliations_choices()),
            set(expected),
        )

    def test_delete_parsed_raw_people(self):
        """
        Check that if a ballot has parsed raw people, user is able to delete them
        """
        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.dulwich_post_ballot,
            uploaded_file="sopn.pdf",
        )
        RawPeople.objects.create(
            ballot=self.dulwich_post_ballot,
            data=[{"name": "Bart", "party_id": "PP52"}],
            source_type=RawPeople.SOURCE_PARSED_PDF,
        )
        raw_people = RawPeople.objects.filter(ballot=self.dulwich_post_ballot)
        self.assertEqual(raw_people.count(), 1)
        response = self.app.get(
            "/bulk_adding/sopn/parl.65808.2015-05-07/", user=self.user
        )
        response = response.forms["delete-parsed-people"].submit()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, self.dulwich_post_ballot.get_bulk_add_url()
        )
        with self.assertRaises(RawPeople.DoesNotExist):
            RawPeople.objects.get(ballot=self.dulwich_post_ballot)
        logged_actions = LoggedAction.objects.filter(
            ballot=self.dulwich_post_ballot,
            user=self.user,
            action_type=ActionType.DELETED_PARSED_RAW_PEOPLE,
            edit_type=EditType.USER.name,
        )
        self.assertEqual(logged_actions.count(), 1)

    def test_delete_raw_people_not_available(self):
        """
        Check that if a ballot has raw people but they were not parsed by a bot
        the form to delete them is not on the page
        """
        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.dulwich_post_ballot,
            uploaded_file="sopn.pdf",
        )
        RawPeople.objects.create(
            ballot=self.dulwich_post_ballot,
            data=[{"name": "Bart", "party_id": "PP52"}],
            source_type=RawPeople.SOURCE_BULK_ADD_FORM,
        )
        raw_people = RawPeople.objects.filter(ballot=self.dulwich_post_ballot)
        self.assertEqual(raw_people.count(), 1)
        response = self.app.get(
            "/bulk_adding/sopn/parl.65808.2015-05-07/", user=self.user
        )
        with self.assertRaises(KeyError):
            response.forms["delete-parsed-people"]

    def test_bulk_add_person_removes_spaces_from_name(self):
        """Test that spaces are removed from the name field when bulk adding people"""
        OfficialDocument.objects.create(
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            ballot=self.dulwich_post_ballot,
            uploaded_file="sopn.pdf",
        )
        # create a party that isnt included in the default_party_choices as it
        # doesnt have any current candidates
        PartyFactory(
            ec_id="PP530",
            name="Barnsley Independent Group",
            legacy_slug="party:530",
            register="GB",
            current_candidates=0,
        )
        request = self.app.get(
            "/bulk_adding/sopn/parl.65808.2015-05-07/", user=self.user
        )

        form = request.forms["bulk_add_form"]
        form["form-0-name"] = "    Bart Simpson    "
        form["form-0-party_1"] = self.green_party.ec_id
        resp = form.submit()
        self.assertEqual(resp.status_code, 302)
        resp = resp.follow()
        self.assertContains(resp, "Review candidates")
        resp = form.submit()
        self.assertContains(resp, "Bart Simpson")
