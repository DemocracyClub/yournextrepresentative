from django_webtest import WebTest
from sorl.thumbnail import get_thumbnail
from unittest.mock import patch

from candidates.models import LoggedAction
from candidates.models.db import ActionType
from candidates.tests.factories import faker_factory
from candidates.tests.uk_examples import UK2015ExamplesMixin
from candidates.tests.helpers import TmpMediaRootMixin
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME
from people.models import Person, PersonImage
from people.tests.factories import PersonFactory
from popolo.models import Membership
from django.contrib.auth import get_user_model


class TestPersonModels(UK2015ExamplesMixin, TmpMediaRootMixin, WebTest):
    def test_get_display_image_url(self):
        person = PersonFactory(name=faker_factory.name())

        self.assertEqual(
            person.get_display_image_url(),
            "/static/candidates/img/blank-person.png",
        )

        pi = PersonImage.objects.create_from_file(
            EXAMPLE_IMAGE_FILENAME,
            "images/jowell-pilot.jpg",
            defaults={
                "person": person,
                "source": "Taken from Wikipedia",
                "copyright": "example-license",
                "user_notes": "A photo of Tessa Jowell",
            },
        )

        url = get_thumbnail(pi.image, "x64").url
        # fresh lookup of the instance is required in order to invalidate the
        # cached value of person_image
        person = Person.objects.get()
        self.assertEqual(person.get_display_image_url(), url)

    def test_get_alive_now(self):
        alive_person = PersonFactory(name=faker_factory.name())
        PersonFactory(name=faker_factory.name(), death_date="2016-01-01")
        qs = Person.objects.alive_now()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get(), alive_person)

    def test_current_elections_standing_down(self):
        person = PersonFactory(name=faker_factory.name())
        self.assertEqual(person.current_elections_standing_down(), [])
        Membership.objects.create(
            ballot=self.dulwich_post_ballot_earlier,
            party=self.ld_party,
            person=person,
            elected=True,
        )

        person.not_standing.add(self.election)
        self.assertEqual(
            person.current_elections_standing_down(), [self.election]
        )

    def test_delete_with_logged_action(self):
        """
        Test that the Person.delete_with_logged_action deletes the objects and
        creates a single logged action with the user assigned
        """
        person = PersonFactory()
        person_pk = person.pk
        user = get_user_model().objects.create()

        person.delete_with_logged_action(
            user=user, source="Test a single logged action is created"
        )
        logged_actions = LoggedAction.objects.filter(
            person_pk=person_pk, action_type=ActionType.PERSON_DELETE
        )

        self.assertEqual(logged_actions.count(), 1)
        self.assertEqual(logged_actions.first().user, user)
        self.assertFalse(Person.objects.filter(pk=person_pk).exists())

    def test_delete_signal(self):
        """
        Test that the standard delete will still create a logged action, but
        without a user
        """
        person = PersonFactory()
        person_pk = person.pk

        person.delete()
        logged_actions = LoggedAction.objects.filter(
            person_pk=person_pk, action_type=ActionType.PERSON_DELETE
        )

        self.assertEqual(logged_actions.count(), 1)
        self.assertIsNone(logged_actions.first().user)
        self.assertFalse(Person.objects.filter(pk=person_pk).exists())

    def test_something_goes_wrong_with_delete(self):
        """
        If the person delete fails for some reason check the logged action was
        not created becasue we are using transaction.atomic
        """
        person = PersonFactory()
        person_pk = person.pk
        user = get_user_model().objects.create()

        with patch.object(person, "delete", side_effect=Exception):
            # catch the exception so we can do
            try:
                person.delete_with_logged_action(
                    user=user, source="Test a logged action isnt created"
                )
            except Exception:
                self.assertFalse(
                    LoggedAction.objects.filter(
                        person_pk=person_pk,
                        action_type=ActionType.PERSON_DELETE,
                    ).exists()
                )
