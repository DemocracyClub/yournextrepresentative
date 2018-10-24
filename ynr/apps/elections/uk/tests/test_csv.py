from django.test import TestCase

import people.tests.factories
from candidates.models import PersonRedirect
from candidates.tests import factories
from candidates.tests.uk_examples import UK2015ExamplesMixin

from people.models import Person


class CSVTests(UK2015ExamplesMixin, TestCase):
    def setUp(self):
        super().setUp()
        # The second person's name (and party name) have diacritics in
        # them to test handling of Unicode when outputting to CSV.
        self.gb_person = people.tests.factories.PersonFactory.create(
            id=2009,
            name="Tessa Jowell",
            honorific_suffix="DBE",
            honorific_prefix="Ms",
            email="jowell@example.com",
            gender="female",
        )
        factories.MembershipFactory.create(
            person=self.gb_person,
            post=self.camberwell_post,
            party=self.labour_party,
            post_election=self.camberwell_post_pee,
        )
        factories.MembershipFactory.create(
            person=self.gb_person,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.camberwell_post_pee_earlier,
        )
        self.gb_person.identifiers.create(
            identifier="uk.org.publicwhip/person/10326",
            scheme="uk.org.publicwhip",
        )

    def test_as_list_single_dict(self):
        PersonRedirect.objects.create(old_person_id=33, new_person_id=2009)
        PersonRedirect.objects.create(old_person_id=44, new_person_id=2009)
        person = Person.objects.joins_for_csv_output().get(pk=self.gb_person.id)
        # After the select_related and prefetch_related calls
        # PersonExtra there should only be one more query - that to
        # find the complex fields mapping:
        redirects = PersonRedirect.all_redirects_dict()
        with self.assertNumQueries(0):
            person_dict_list = person.as_list_of_dicts(
                self.election, redirects=redirects
            )
        self.assertEqual(len(person_dict_list), 1)
        person_dict = person_dict_list[0]
        self.assertEqual(len(person_dict), 37)
        self.assertEqual(person_dict["id"], 2009)

        # Test the extra CSV fields:
        self.assertEqual(person_dict["gss_code"], "")
        self.assertEqual(
            person_dict["parlparse_id"], "uk.org.publicwhip/person/10326"
        )
        self.assertEqual(
            person_dict["theyworkforyou_url"],
            "http://www.theyworkforyou.com/mp/10326",
        )
        self.assertEqual(person_dict["party_ec_id"], "PP53")
        self.assertEqual(person_dict["old_person_ids"], "33;44")
