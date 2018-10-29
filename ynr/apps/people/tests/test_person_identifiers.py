from django_webtest import WebTest

from people.tests.factories import PersonFactory
from people.models import PersonIdentifier


class TestPersonIdentifiers(WebTest):
    def test_str(self):
        person = PersonFactory(pk=1)
        pi = PersonIdentifier.objects.create(
            person=person,
            value="@democlub",
            value_type="Twitter Username",
            internal_identifier="2324",
        )
        self.assertEqual(str(pi), "1: Twitter Username (@democlub)")
