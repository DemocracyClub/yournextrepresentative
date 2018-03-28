from django.core.management import call_command
from django_webtest import WebTest

from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from candidates.models import LoggedAction


class TestBulkAddingByParty(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super(TestBulkAddingByParty, self).setUp()
        call_command('rebuild_index', verbosity=0, interactive=False)

    def test_party_select(self):
        response = self.app.get(
            '/bulk_adding/party/2015/',
            user=self.user_who_can_upload_documents
        )

        self.assertContains(
            response,
            'GB Parties'
        )

    def test_party_select_invalid_party(self):
        form = self.app.get(
            '/bulk_adding/party/2015/',
            user=self.user_who_can_upload_documents
        ).forms[1]
        form['party_gb'] = ''
        response = form.submit()
        self.assertContains(
            response,
            "Select one and only one party"
        )


    def test_submit_party_redirects_to_person_form(self):
        form = self.app.get(
            '/bulk_adding/party/2015/',
            user=self.user_who_can_upload_documents
        ).forms[1]
        form['party_gb'] = self.conservative_party_extra.base.pk
        response = form.submit().follow()

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertContains(
            response,
            'Add Conservative Party candidates'
        )

        self.assertEqual(
            response.context['election_obj'],
            self.election
        )

        self.assertEqual(
            response.context['party'].extra,
            self.conservative_party_extra
        )

        self.assertTrue(
            len(response.context['posts']),
            2
        )

        self.assertContains(
            response,
            "Camberwell and Peckham"
        )

        self.assertContains(
            response,
            "1 seat contested."
        )

        self.assertContains(
            response,
            "No Conservative Party candidates know yet."
        )

    def test_submit_name_for_area_without_source(self):
        pee = self.election.postextraelection_set.first()
        form = self.app.get(
            '/bulk_adding/party/2015/PP52/',
            user=self.user_who_can_upload_documents
        ).forms[1]

        form['{}-0-name'.format(pee.pk)] = "Pemphero Pasternak"

        response = form.submit()
        self.assertContains(
            response,
            "This field is required"
        )

    def test_submit_name_for_area_without_any_names(self):
        form = self.app.get(
            '/bulk_adding/party/2015/PP52/',
            user=self.user_who_can_upload_documents
        ).forms[1]

        form['source'] = "https://example.com/candidates/"

        response = form.submit()
        self.assertContains(
            response,
            "Please enter at least one name"
        )

    def test_submit_name_for_area(self):
        pee = self.election.postextraelection_set.first()

        # Make sure we have no people or logged actions
        self.assertEqual(pee.postextra.base.memberships.count(), 0)
        self.assertEqual(LoggedAction.objects.count(), 0)

        form = self.app.get(
            '/bulk_adding/party/2015/PP52/',
            user=self.user_who_can_upload_documents
        ).forms[1]

        self.assertEqual(
            len(form.fields),
            23
        )

        form['source'] = "https://example.com/candidates/"
        form['{}-0-name'.format(pee.pk)] = "Pemphero Pasternak"

        response = form.submit().follow()

        self.assertContains(
            response,
            "Add <strong>Pemphero Pasternak</strong> as a new person"
        )

        form = response.forms[1]

        # Test that the form raises and error if nothing is selected
        response = form.submit()
        self.assertContains(
            response,
            "This field is required."
        )

        # Not submit the valid form
        form["{}-0-select_person".format(pee.pk)] = '_new'
        form.submit()

        # We should have a new person and membership
        self.assertTrue(
            pee.postextra.base.memberships.first().person.name,
            "Pemphero Pasternak"
        )

        # We should have a new person and membership
        self.assertTrue(
            pee.postextra.base.memberships.first().person.name,
            "Pemphero Pasternak"
        )

        # We should have created 2 logged actions, one for person-create
        # and one for person-update (adding the membership)
        self.assertEqual(
            LoggedAction.objects.count(),
            2
        )
