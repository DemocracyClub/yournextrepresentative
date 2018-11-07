import json

from django.core.management import call_command
from django_webtest import WebTest

import people.tests.factories
from popolo.models import Membership
from people.models import Person

from candidates.tests import factories
from candidates.tests.auth import TestUserMixin
from candidates.tests.test_update_view import membership_id_set
from candidates.tests.uk_examples import UK2015ExamplesMixin
from official_documents.models import OfficialDocument


class TestBulkAdding(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        call_command("rebuild_index", verbosity=0, interactive=False)

    def testNoFormIfNoSopn(self):
        response = self.app.get(
            "/bulk_adding/sopn/2015/65808/",
            user=self.user_who_can_upload_documents,
        )

        self.assertContains(
            response, "This post doesn't have a nomination paper"
        )

        self.assertNotContains(response, "Review")

    def testFormIfSopn(self):
        post = self.dulwich_post

        OfficialDocument.objects.create(
            election=self.election,
            post=post,
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            post_election=self.dulwich_post_pee,
            uploaded_file="sopn.pdf",
        )

        response = self.app.get(
            "/bulk_adding/sopn/2015/65808/",
            user=self.user_who_can_upload_documents,
        )

        self.assertNotContains(
            response, "This post doesn't have a nomination paper"
        )

        self.assertContains(response, "Review")

    def test_submitting_form(self):
        post = self.dulwich_post

        OfficialDocument.objects.create(
            election=self.election,
            post=post,
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            post_election=self.dulwich_post_pee,
            uploaded_file="sopn.pdf",
        )

        response = self.app.get("/bulk_adding/sopn/2015/65808/", user=self.user)

        form = response.forms["bulk_add_form"]
        form["form-0-name"] = "Homer Simpson"
        form["form-0-party"] = self.green_party.ec_id

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
        with self.assertNumQueries(58):
            response = form.submit()

        self.assertEqual(Person.objects.count(), 1)
        homer = Person.objects.get()
        self.assertEqual(homer.name, "Homer Simpson")
        homer_versions = json.loads(homer.versions)
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

    def test_adding_to_existing_person(self):
        existing_person = people.tests.factories.PersonFactory.create(
            id="1234567", name="Bart Simpson"
        )
        existing_membership = factories.MembershipFactory.create(
            person=existing_person,
            post=self.local_post,
            party=self.labour_party,
            post_election=self.local_election.postextraelection_set.get(
                post=self.local_post
            ),
        )
        memberships_before = membership_id_set(existing_person)
        # Now try adding that person via bulk add:
        OfficialDocument.objects.create(
            election=self.election,
            post=self.dulwich_post,
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            post_election=self.dulwich_post_pee,
            uploaded_file="sopn.pdf",
        )

        response = self.app.get("/bulk_adding/sopn/2015/65808/", user=self.user)

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

    def test_adding_to_existing_person_same_election(self):
        # This could happen if someone's missed that there was the
        # same person already listed on the first page, but then
        # spotted them on the review page and said to merge them then.
        existing_person = people.tests.factories.PersonFactory.create(
            id="1234567", name="Bart Simpson"
        )
        existing_membership = factories.MembershipFactory.create(
            person=existing_person,
            # !!! This is the line that differs from the previous test:
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.election.postextraelection_set.get(
                post=self.dulwich_post
            ),
        )
        memberships_before = membership_id_set(existing_person)
        # Now try adding that person via bulk add:
        OfficialDocument.objects.create(
            election=self.election,
            post=self.dulwich_post,
            source_url="http://example.com",
            document_type=OfficialDocument.NOMINATION_PAPER,
            post_election=self.dulwich_post_pee,
            uploaded_file="sopn.pdf",
        )

        response = self.app.get("/bulk_adding/sopn/2015/65808/", user=self.user)

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
        response = self.app.get("/bulk_adding/2015/65808/", user=self.user)

        self.assertEqual(response.status_code, 302)
