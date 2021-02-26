from django.test.client import RequestFactory
from django_webtest import WebTest

from bulk_adding import helpers
from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin


class TestBulkAddingByParty(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def test_add_person(self):

        request = self.factory.get("/")
        request.user = self.user

        person_data = {"name": "Foo", "source": "example.com"}

        with self.assertNumQueries(6):
            helpers.add_person(request, person_data)
