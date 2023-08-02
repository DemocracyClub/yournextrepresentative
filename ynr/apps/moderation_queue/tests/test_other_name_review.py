from candidates.tests.auth import TestUserMixin
from candidates.tests.factories import MembershipFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin
from django.contrib.auth.models import Group, User
from django.urls import reverse
from django_webtest import WebTest
from people.models import TRUSTED_TO_EDIT_NAME
from people.tests.factories import PersonFactory
from popolo.models import OtherName


class OtherNameReviewTests(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        self.person = PersonFactory.create(id=2009, name="Tessa Jowell")
        self.other_name = self.person.other_names.create(
            name="Tessa Palmer", needs_review=True
        )
        MembershipFactory.create(
            person=self.person,
            post=self.dulwich_post,
            party=self.labour_party,
            ballot=self.dulwich_post_ballot,
        )
        self.group = Group.objects.get(name=TRUSTED_TO_EDIT_NAME)
        self.user_who_can_name_review: User = self.user
        self.user_who_can_name_review.groups.add(self.group)

    def test_name_edit_page_approve(self):
        resp = self.app.get(
            reverse("person-name-review"), user=self.user_who_can_name_review
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Set as primary name")

        form = resp.forms[f"review_name_form_{self.other_name.pk}"]
        form.submit(name="decision_approve")
        self.person.refresh_from_db()
        self.assertEqual(self.person.name, "Tessa Palmer")
        self.assertFalse(OtherName.objects.filter(needs_review=True).exists())

    def test_name_edit_page_reject(self):
        resp = self.app.get(
            reverse("person-name-review"), user=self.user_who_can_name_review
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Keep as other name")

        form = resp.forms[f"review_name_form_{self.other_name.pk}"]
        form.submit(name="decision_reject")
        self.person.refresh_from_db()
        self.assertEqual(self.person.name, "Tessa Jowell")
        self.assertFalse(OtherName.objects.filter(needs_review=True).exists())

    def test_name_edit_page_delete(self):
        resp = self.app.get(
            reverse("person-name-review"), user=self.user_who_can_name_review
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Delete")

        form = resp.forms[f"review_name_form_{self.other_name.pk}"]
        form.submit(name="decision_delete")
        self.person.refresh_from_db()
        self.assertEqual(self.person.name, "Tessa Jowell")
        self.assertFalse(OtherName.objects.exists())

    def test_approve_name_keeps_previous_name(self):
        self.person.name = "Foo Bar"
        self.person.save()

        resp = self.app.get(
            reverse("person-name-review"), user=self.user_who_can_name_review
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Set as primary name")

        form = resp.forms[f"review_name_form_{self.other_name.pk}"]
        form.submit(name="decision_approve")

        self.person.refresh_from_db()
        self.assertEqual(
            set(self.person.other_names.all().values_list("name", flat=True)),
            {"Foo Bar"},
        )
        self.assertEqual(self.person.name, "Tessa Palmer")
