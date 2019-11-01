import json

from django.utils.six.moves.urllib_parse import urlsplit
from django_webtest import WebTest
from webtest.forms import Text

from people.models import Person
from people.tests.factories import PersonFactory
from popolo.models import Membership

from .auth import TestUserMixin
from .factories import MembershipFactory
from .uk_examples import UK2015ExamplesMixin


def membership_id_set(person):
    return set(person.memberships.values_list("pk", flat=True))


class TestUpdatePersonView(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()
        person = PersonFactory.create(id=2009, name="Tessa Jowell")

        MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.green_party,
            ballot=self.dulwich_post_ballot,
        )

    def test_update_person_should_not_lose_existing_not_standing(self):
        # Pretend that we know she wasn't standing in the earlier election:
        tessa = Person.objects.get(pk=2009)
        tessa.not_standing.add(self.earlier_election)
        response = self.app.get("/person/2009/update", user=self.user)
        form = response.forms["person-details"]
        form.submit()
        self.assertEqual(
            list(tessa.not_standing.all()), [self.earlier_election]
        )

    def test_update_person_view_get_without_login(self):
        response = self.app.get("/person/2009/update")
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual("/accounts/login/", split_location.path)
        self.assertEqual("next=/person/2009/update", split_location.query)

    def test_update_person_view_get_refused_copyright(self):
        response = self.app.get("/person/2009/update", user=self.user_refused)
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual("/copyright-question", split_location.path)
        self.assertEqual("next=/person/2009/update", split_location.query)

    def test_update_person_view_get(self):
        # For the moment just check that the form's actually there:
        response = self.app.get("/person/2009/update", user=self.user)
        form = response.forms["person-details"]
        self.assertIsNotNone(form)

    def test_update_person_submission_copyright_refused(self):
        response = self.app.get("/person/2009/update", user=self.user)
        form = response.forms["person-details"]
        form[
            "tmp_person_identifiers-0-value"
        ] = "http://en.wikipedia.org/wiki/Tessa_Jowell"
        form["tmp_person_identifiers-0-value_type"] = "wikipedia_url"
        form["party_GB_parl.2015-05-07"] = self.labour_party.ec_id
        form["source"] = "Some source of this information"
        submission_response = form.submit(user=self.user_refused)
        split_location = urlsplit(submission_response.location)
        self.assertEqual("/copyright-question", split_location.path)
        self.assertEqual("next=/person/2009/update", split_location.query)

    def test_update_person_submission(self):
        memberships_before = membership_id_set(Person.objects.get(pk=2009))
        response = self.app.get(
            "/person/2009/update", user=self.user_who_can_lock
        )
        form = response.forms["person-details"]
        form[
            "tmp_person_identifiers-0-value"
        ] = "http://en.wikipedia.org/wiki/Tessa_Jowell"
        form["tmp_person_identifiers-0-value_type"] = "wikipedia_url"

        form["party_GB_parl.2015-05-07"] = self.labour_party.ec_id
        form["source"] = "Some source of this information"
        submission_response = form.submit()

        person = Person.objects.get(id="2009")
        party = person.memberships.all()

        self.assertEqual(party.count(), 1)
        self.assertEqual(party[0].party.legacy_slug, "party:53")
        self.assertEqual(party[0].party.ec_id, "PP53")

        person_identifiers = person.tmp_person_identifiers.all()
        self.assertEqual(person_identifiers.count(), 1)
        self.assertEqual(
            person_identifiers[0].value,
            "http://en.wikipedia.org/wiki/Tessa_Jowell",
        )

        # It should redirect back to the same person's page:
        split_location = urlsplit(submission_response.location)
        self.assertEqual("/person/2009", split_location.path)
        self.assertEqual(memberships_before, membership_id_set(person))

    def test_update_dd_mm_yyyy_birth_date(self):
        memberships_before = membership_id_set(Person.objects.get(pk=2009))
        response = self.app.get(
            "/person/2009/update", user=self.user_who_can_lock
        )
        form = response.forms["person-details"]
        form["birth_date"] = "1/4/1875"
        form["source"] = "An update for testing purposes"
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual("/person/2009", split_location.path)

        person = Person.objects.get(id="2009")
        self.assertEqual(person.birth_date, "1875-04-01")
        self.assertEqual(memberships_before, membership_id_set(person))

    def test_update_person_extra_fields(self):
        memberships_before = membership_id_set(Person.objects.get(pk=2009))

        response = self.app.get(
            "/person/2009/update", user=self.user_who_can_lock
        )
        form = response.forms["person-details"]
        form["birth_date"] = "1/4/1875"
        form["source"] = "An update for testing purposes"
        response = form.submit()

        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual("/person/2009", split_location.path)

        person = Person.objects.get(id="2009")
        self.assertEqual(person.birth_date, "1875-04-01")
        versions_data = json.loads(person.versions)
        self.assertEqual(
            versions_data[0]["data"]["extra_fields"], {"favourite_biscuits": ""}
        )
        self.assertEqual(memberships_before, membership_id_set(person))

    def test_update_person_add_new_candidacy(self):
        memberships_before = membership_id_set(Person.objects.get(pk=2009))
        response = self.app.get("/person/2009/update", user=self.user)
        # Now fake the addition of elements to the form as would
        # happen with the Javascript addition of a new candidacy.
        form = response.forms["person-details"]
        extra_fields = [
            ("extra_election_id", "local.maidstone.2016-05-05"),
            ("party_GB_local.maidstone.2016-05-05", self.labour_party.ec_id),
            ("constituency_local.maidstone.2016-05-05", "DIW:E05005004"),
            ("standing_local.maidstone.2016-05-05", "standing"),
            ("source", "Testing dynamic election addition"),
        ]
        start_pos = len(form.field_order)
        for pos, data in enumerate(extra_fields):
            name, value = data
            field = Text(form, "input", name, start_pos + pos, value)
            form.field_order.append((name, field))
            form.fields[name] = [field]
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual("/person/2009", split_location.path)

        person = Person.objects.get(pk=2009)
        memberships_afterwards = membership_id_set(person)
        extra_membership_ids = memberships_afterwards - memberships_before
        self.assertEqual(len(extra_membership_ids), 1)
        new_candidacy = Membership.objects.get(pk=list(extra_membership_ids)[0])
        self.assertEqual(new_candidacy.post.label, "Shepway South Ward")
        self.assertEqual(
            new_candidacy.ballot.election.slug, "local.maidstone.2016-05-05"
        )
        self.assertEqual(new_candidacy.party.name, "Labour Party")
        same_before_and_after = memberships_before & memberships_afterwards
        self.assertEqual(len(same_before_and_after), 1)

    def test_update_person_add_new_candidacy_unsure_if_standing(self):
        memberships_before = membership_id_set(Person.objects.get(pk=2009))
        response = self.app.get("/person/2009/update", user=self.user)
        # Now fake the addition of elements to the form as would
        # happen with the Javascript addition of a new candidacy.
        form = response.forms["person-details"]
        extra_fields = [
            ("extra_election_id", "local.maidstone.2016-05-05"),
            ("party_GB_local.maidstone.2016-05-05", self.labour_party.ec_id),
            ("constituency_local.maidstone.2016-05-05", "DIW:E05005004"),
            ("standing_local.maidstone.2016-05-05", "not-sure"),
            ("source", "Testing dynamic election addition"),
        ]
        starting_pos = len(form.field_order)
        for pos, data in enumerate(extra_fields):
            name, value = data
            field = Text(form, "input", None, starting_pos + pos, value)
            form.fields[name] = [field]
            form.field_order.append((name, field))
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual("/person/2009", split_location.path)

        person = Person.objects.get(pk=2009)
        memberships_afterwards = membership_id_set(person)
        membership_ids = memberships_afterwards - memberships_before
        self.assertEqual(len(membership_ids), 0)
