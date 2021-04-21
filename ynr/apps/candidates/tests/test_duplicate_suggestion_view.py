from django.test.client import RequestFactory
from django.test.testcases import TestCase
from django.urls.base import reverse
from django_webtest import WebTest
import pytest
from candidates.tests.auth import TestUserMixin

from candidates.views.people import DuplicatePersonView
from duplicates.models import DuplicateSuggestion
from people.models import Person
from people.tests.factories import PersonFactory


class TestDuplicatePersonViewUnitTests(TestUserMixin, TestCase):
    def setUp(self):
        super().setUp()
        rf = RequestFactory()
        request = rf.get("/")
        request.GET = {}
        request.user = self.user_who_can_merge
        view = DuplicatePersonView()
        view.setup(request=request)
        view.object = Person(pk=1)
        self.view = view

    def test_get_context_data_missing_other_param(self):
        context = self.view.get_context_data()
        assert "error" in context
        assert context["error"] == "Other person ID is missing"

    def test_get_context_data_missing_other_value(self):
        self.view.request.GET.update({"other": None})
        context = self.view.get_context_data()
        assert "error" in context
        assert context["error"] == "Other person ID is missing"

    def test_get_context_data_other_not_number(self):
        self.view.request.GET.update({"other": "foo"})
        context = self.view.get_context_data()
        assert "error" in context
        assert context["error"] == "Malformed person ID foo"

    def test_get_context_data_other_id_same_as_person(self):
        self.view.request.GET.update({"other": "1"})
        context = self.view.get_context_data()
        assert "error" in context
        assert (
            context["error"] == "You can't merge a person (1) with themself (1)"
        )

    def test_get_context_data_other_person_not_found(self):
        self.view.request.GET.update({"other": "2"})
        context = self.view.get_context_data()
        assert "error" in context
        assert context["error"] == "Person not found with ID 2"

    def test_get_context_data_other_person_added_to_context(self):
        person = PersonFactory(pk=1234)
        self.view.request.GET.update({"other": "1234"})
        context = self.view.get_context_data()
        assert "error" not in context
        assert context["other_person"] == person
        assert context["user_can_merge"] is True

    def test_get_context_data_other_person_added_to_context_user_cant_merge(
        self,
    ):
        person = PersonFactory(pk=1234)
        self.view.request.user = self.user
        self.view.request.GET.update({"other": "1234"})
        context = self.view.get_context_data()
        assert "error" not in context
        assert context["other_person"] == person
        assert context["user_can_merge"] is False


class TestDuplicatePersonViewIntegrationTests(TestUserMixin, WebTest, TestCase):
    def setUp(self):
        super().setUp()
        self.person = PersonFactory()
        self.other_person = PersonFactory()

    def test_duplicate_suggestion_created(self):
        assert DuplicateSuggestion.objects.count() == 0

        url = reverse(
            viewname="duplicate-person", kwargs={"person_id": self.person.pk}
        )
        url = f"{url}?other={self.other_person.pk}"
        response = self.app.get(url, user=self.user)

        # standard user so merge form should not be displayed
        assert DuplicatePersonView.MERGE_FORM_ID not in response.forms
        assert DuplicatePersonView.SUGGESTION_FORM_ID in response.forms

        # submit the suggestion form and expect object to be created
        suggestion_form = response.forms[DuplicatePersonView.SUGGESTION_FORM_ID]
        response = suggestion_form.submit()

        suggestion = DuplicateSuggestion.objects.filter(
            person=self.person, other_person=self.other_person
        ).first()
        assert DuplicateSuggestion.objects.count() == 1
        assert bool(suggestion) is True

    def test_duplicate_suggestion_not_created(self):
        # created a suggestion from another user
        created_suggestion = DuplicateSuggestion.objects.create(
            person=self.person,
            other_person=self.other_person,
            user=self.user_who_can_merge,
        )
        assert DuplicateSuggestion.objects.count() == 1

        url = reverse(
            viewname="duplicate-person", kwargs={"person_id": self.person.pk}
        )
        url = f"{url}?other={self.other_person.pk}"
        response = self.app.get(url, user=self.user)

        # submit the suggestion form and expect object to be created
        suggestion_form = response.forms[DuplicatePersonView.SUGGESTION_FORM_ID]
        response = suggestion_form.submit()

        # get suggestion - pk should match with one we created
        suggestion = DuplicateSuggestion.objects.filter(
            person=self.person, other_person=self.other_person
        ).first()
        assert DuplicateSuggestion.objects.count() == 1
        assert created_suggestion.pk == suggestion.pk
