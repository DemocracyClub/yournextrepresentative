"""
Merging two people and then splitting them again, through the website,
should leave both people exactly as they were before the merge.
"""

from candidates.models import LoggedAction, PersonRedirect
from candidates.models.db import ActionType
from candidates.models.versions import (
    get_person_as_version_data,
    get_versions_parent_map,
)
from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from candidates.views.version_data import get_change_metadata
from django.urls import reverse
from django_webtest import WebTest
from people.models import Person, PersonImage
from people.tests.factories import PersonFactory
from results.models import ResultEvent
from uk_results.models import CandidateResult, ResultSet


def snapshot(person_id):
    """
    Everything about a person that merging changes, in a comparable form
    """
    person = Person.objects.get(pk=person_id)
    memberships = []
    for m in person.memberships.select_related("ballot", "party").order_by(
        "pk"
    ):
        memberships.append(
            {
                "pk": m.pk,
                "ballot": m.ballot.ballot_paper_id,
                "party": m.party.ec_id,
                "elected": m.elected,
                "party_list_position": m.party_list_position,
                "sopn_first_names": m.sopn_first_names,
                "sopn_last_name": m.sopn_last_name,
                "votes": getattr(
                    CandidateResult.objects.filter(membership=m).first(),
                    "num_ballots",
                    None,
                ),
            }
        )
    try:
        image = person.image.image.name
    except PersonImage.DoesNotExist:
        image = None
    return {
        "pk": person.pk,
        # Name, other names (with notes), identifiers, simple fields,
        # candidacies and "not standing" elections, as the version history
        # records them
        "data": get_person_as_version_data(person),
        "memberships": memberships,
        "result_events": sorted(
            ResultEvent.objects.filter(winner=person).values_list(
                "pk", flat=True
            )
        ),
        "image": image,
    }


class TestMergeThenSplit(TestUserMixin, UK2015ExamplesMixin, WebTest):
    csrf_checks = False

    def record(self, person, source):
        person.record_version(get_change_metadata(None, source, user=self.user))
        person.save()
        version_id = person.versions[0]["version_id"]
        LoggedAction.objects.create(
            user=self.user,
            person=person,
            action_type=ActionType.PERSON_CREATE,
            popit_person_new_version=version_id,
            source=source,
        )

    def setUp(self):
        super().setUp()
        # The person who will be kept by the merge (the lower ID)
        self.jo = PersonFactory(
            name="Jo Smith", gender="male", birth_date="1970"
        )
        self.jo.memberships.create(
            ballot=self.dulwich_post_ballot_earlier,
            party=self.labour_party,
            elected=False,
        )
        self.jo.other_names.create(name="J Smith", note="On a leaflet")
        self.jo.tmp_person_identifiers.create(
            value_type="twitter_username", value="jo_smith"
        )
        self.record(self.jo, "Created Jo")

        # The person who will be merged into Jo and deleted
        self.joanne = PersonFactory(
            name="Joanne Smith", gender="female", favourite_biscuit="Hobnob"
        )
        membership = self.joanne.memberships.create(
            ballot=self.local_ballot,
            party=self.green_party,
            elected=True,
            party_list_position=1,
            sopn_first_names="Joanne",
            sopn_last_name="SMITH",
        )
        result_set = ResultSet.objects.create(
            ballot=self.local_ballot,
            num_turnout_reported=10000,
            num_spoilt_ballots=30,
            user=self.user,
            ip_address="127.0.0.1",
            source="Council results page",
        )
        CandidateResult.objects.create(
            result_set=result_set, membership=membership, num_ballots=1234
        )
        ResultEvent.objects.create(
            election=self.local_election,
            winner=self.joanne,
            post=self.local_post,
            old_post_id=self.local_post.slug,
            winner_party=self.green_party,
            source="Council results page",
        )
        self.joanne.other_names.create(name="Jojo", note="Nickname")
        self.joanne.tmp_person_identifiers.create(
            value_type="twitter_username", value="joanne_smith"
        )
        self.joanne.tmp_person_identifiers.create(
            value_type="email", value="joanne@example.com"
        )
        self.joanne.not_standing.add(self.senedd_election)
        PersonImage.objects.create(
            person=self.joanne, image="joanne.jpg", source="Council website"
        )
        self.record(self.joanne, "Created Joanne")

        self.jo_pk, self.joanne_pk = self.jo.pk, self.joanne.pk
        self.assertLess(self.jo_pk, self.joanne_pk)

    def merge(self):
        response = self.app.post(
            reverse("person-merge", kwargs={"person_id": self.jo_pk}),
            {"other_person": str(self.joanne_pk)},
            user=self.user_who_can_merge,
        )
        self.assertEqual(response.status_code, 302)

    def split(self):
        response = self.app.get(
            reverse("person-split", kwargs={"person_id": self.jo_pk}),
            user=self.user_who_can_split,
        )
        form = response.forms["person-split"]
        form["membership"] = str(
            Person.objects.get(pk=self.jo_pk)
            .memberships.get(ballot=self.local_ballot)
            .pk
        )
        form["destination"] = "new"
        form["move_image"] = True
        response = form.submit("action", value="preview")

        report = response.html.find("table", class_="split-report")
        self.assertIn(f"{self.joanne_pk} (restored)", report.get_text())
        self.assertIn("Ready to split", report.get_text())

        form = response.forms["person-split"]
        form["warnings_checked"] = True
        response = form.submit("action", value="split")
        self.assertEqual(response.status_code, 302)

    def test_merge_then_split_restores_both_people(self):
        jo_before = snapshot(self.jo_pk)
        joanne_before = snapshot(self.joanne_pk)
        jo_versions_before = list(Person.objects.get(pk=self.jo_pk).versions)
        joanne_versions_before = list(
            Person.objects.get(pk=self.joanne_pk).versions
        )
        actions_before = {
            action.pk: action.person_id for action in LoggedAction.objects.all()
        }

        self.merge()

        # Check the merge really did combine them, so the split has
        # something to undo
        self.assertFalse(Person.objects.filter(pk=self.joanne_pk).exists())
        merged = snapshot(self.jo_pk)
        self.assertEqual(len(merged["memberships"]), 2)
        self.assertEqual(merged["data"]["gender"], "female")
        self.assertEqual(merged["image"], "joanne.jpg")
        self.assertTrue(
            PersonRedirect.objects.filter(
                old_person_id=self.joanne_pk, new_person_id=self.jo_pk
            ).exists()
        )

        self.split()

        # Both people are back as they were
        self.assertEqual(snapshot(self.jo_pk), jo_before)
        self.assertEqual(snapshot(self.joanne_pk), joanne_before)

        # Joanne's old URL works again rather than redirecting to Jo
        self.assertFalse(
            PersonRedirect.objects.filter(old_person_id=self.joanne_pk).exists()
        )

        # Their logged actions are back with the right person
        for action_pk, person_id in actions_before.items():
            self.assertEqual(
                LoggedAction.objects.get(pk=action_pk).person_id, person_id
            )

        # Version history: Joanne gets hers back under the split version,
        # and Jo's history is only added to
        jo = Person.objects.get(pk=self.jo_pk)
        joanne = Person.objects.get(pk=self.joanne_pk)
        self.assertEqual(joanne.versions[1:], joanne_versions_before)
        self.assertEqual(
            joanne.versions[0]["information_source"],
            f"Restored by splitting candidacy "
            f"{self.local_ballot.ballot_paper_id} off person {self.jo_pk}",
        )
        jo_version_ids = [v["version_id"] for v in jo.versions]
        for version in jo_versions_before:
            self.assertIn(version["version_id"], jo_version_ids)
        # Both histories can still be shown on the person's page
        get_versions_parent_map(jo.versions)
        get_versions_parent_map(joanne.versions)
