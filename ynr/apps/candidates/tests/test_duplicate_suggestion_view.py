from django.test.client import RequestFactory
from django.test.testcases import TestCase
from django.urls.base import reverse
from django_webtest import WebTest
import pytest
from candidates.tests.auth import TestUserMixin

from candidates.views.people import DuplicatePersonView
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
        self
    ):
        person = PersonFactory(pk=1234)
        self.view.request.user = self.user
        self.view.request.GET.update({"other": "1234"})
        context = self.view.get_context_data()
        assert "error" not in context
        assert context["other_person"] == person
        assert context["user_can_merge"] is False
