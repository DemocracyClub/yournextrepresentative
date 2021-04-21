from django.test.client import RequestFactory
from django.test.testcases import TestCase
from django.urls.base import reverse
from django_webtest import WebTest
from mock import patch, MagicMock

from candidates.tests.auth import TestUserMixin
from candidates.views.people import DuplicatePersonView
from duplicates.models import DuplicateSuggestion
from people.models import Person
from people.tests.factories import PersonFactory


class TestDuplicatePersonViewUnitTests(TestUserMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.rf = RequestFactory()
        request = self.rf.get("/")
        request.GET = {}
        request.user = self.user_who_can_merge
        view = DuplicatePersonView()
        view.setup(request=request)
        view.object = Person(pk=1)
        self.view = view

    def test_get_context_data_user_cant_merge(self):
        self.view.request.user = self.user
        context = self.view.get_context_data()
        self.assertFalse(context["user_can_merge"])

    def test_get_context_data_user_can_merge(self):
        self.view.request.user = self.user_who_can_merge
        context = self.view.get_context_data()
        self.assertTrue(context["user_can_merge"])

    def test_post_calls_get_object(self):
        with patch.object(self.view, "get_object") as mock:
            mock.return_value = Person(pk=2)
            self.view.post(request=self.view.request)
            mock.assert_called_once()

    @patch("candidates.views.DuplicatePersonView.get_context_data")
    @patch("candidates.views.DuplicatePersonView.get_object")
    def test_get_checks_form_valid(self, object_mock, context_mock):
        for boolean in [True, False]:
            with self.subTest(msg=f"Error {boolean}"):
                object_mock.return_value = Person(pk=2)
                form = MagicMock()
                form.is_valid.return_value = boolean
                fake_context = {"form": form}
                context_mock.return_value = fake_context

                self.view.get(request=self.view.request)
                object_mock.assert_called_once()
                context_mock.assert_called_once()
                form.is_valid.assert_called_once()
                should_have_errors = not boolean
                assert should_have_errors is bool(fake_context.get("errors"))

    def test_get_form_kwargs(self):
        """
        Test that both get or post request have same kwargs added
        """
        get_request = self.rf.get("/")
        get_request.GET = {"other_person": "2"}
        get_request.user = self.user

        post_request = self.rf.post("/")
        post_request.POST = {"other_person": "2"}
        post_request.user = self.user

        for request in [get_request, post_request]:
            with self.subTest(msg=request):
                self.view.request = request
                kwargs = self.view.get_form_kwargs()
                assert kwargs["user"] == self.user
                assert kwargs["person"] == self.view.object
                assert "data" in kwargs
                assert kwargs["data"]["other_person"] == "2"


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
        url = f"{url}?other_person={self.other_person.pk}"
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

    def test_duplicate_suggestion_already_open(self):
        # created an open suggestion from another user
        created_suggestion = DuplicateSuggestion.objects.create(
            person=self.person,
            other_person=self.other_person,
            user=self.user_who_can_merge,
            status=DuplicateSuggestion.SUGGESTED,
        )
        assert DuplicateSuggestion.objects.count() == 1

        url = reverse(
            viewname="duplicate-person", kwargs={"person_id": self.person.pk}
        )
        url = f"{url}?other_person={self.other_person.pk}"
        response = self.app.get(url, user=self.user)

        self.assertContains(
            response, "A suggestion between these people is already open"
        )

    def test_duplicate_suggestion_already_rejected(self):
        # create a suggestion that was marked not duplicate
        created_suggestion = DuplicateSuggestion.objects.create(
            person=self.person,
            other_person=self.other_person,
            user=self.user_who_can_merge,
            status=DuplicateSuggestion.NOT_DUPLICATE,
        )
        assert DuplicateSuggestion.objects.count() == 1

        url = reverse(
            viewname="duplicate-person", kwargs={"person_id": self.person.pk}
        )
        url = f"{url}?other_person={self.other_person.pk}"
        response = self.app.get(url, user=self.user)

        self.assertContains(
            response,
            "A suggestion between these two people has already been checked and rejected as not duplicate",
        )
