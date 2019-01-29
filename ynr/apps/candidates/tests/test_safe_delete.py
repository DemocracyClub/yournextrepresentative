from django.test import TestCase

from candidates.models.popolo_extra import (
    UnsafeToDelete,
    model_has_related_objects,
    raise_if_unsafe_to_delete,
)
from people.tests.factories import PersonFactory


class TestSafeDelete(TestCase):
    def test_can_delete(self):
        person = PersonFactory()
        raise_if_unsafe_to_delete(person)
        self.assertFalse(model_has_related_objects(person))

    def test_cant_delete(self):
        person = PersonFactory()
        person.tmp_person_identifiers.create(
            value="foo@example.com", value_type="email"
        )
        with self.assertRaises(UnsafeToDelete):
            raise_if_unsafe_to_delete(person)
