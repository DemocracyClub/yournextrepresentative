import re

from django_webtest import WebTest

from people.models import Person, PersonNameSynonym

from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from people.tests.factories import PersonFactory
from search.utils import search_person_by_name


class TestSearchView(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def test_search_page(self):
        # we have to create the candidate by submitting the form as otherwise
        # we're not making sure the index update hook fires
        response = self.app.get("/search?q=Elizabeth")
        # have to use re to avoid matching search box
        self.assertFalse(re.search(r"""<a[^>]*>Elizabeth""", response.text))

        self.assertFalse(re.search(r"""<a[^>]*>Mr Darcy""", response.text))

        response = self.app.get(
            self.dulwich_post_ballot.get_absolute_url(), user=self.user
        )
        form = response.forms["new-candidate-form"]
        form["name"] = "Mr Darcy"
        form["tmp_person_identifiers-0-value"] = "darcy@example.com"
        form["tmp_person_identifiers-0-value_type"] = "email"
        form["source"] = "Testing adding a new person to a post"
        form["party_identifier"] = self.labour_party.ec_id
        form.submit()

        response = self.app.get(
            self.dulwich_post_ballot.get_absolute_url(), user=self.user
        )
        form = response.forms["new-candidate-form"]
        form["name"] = "Elizabeth Bennet"
        form["tmp_person_identifiers-0-value"] = "lizzie@example.com"
        form["tmp_person_identifiers-0-value_type"] = "email"
        form["source"] = "Testing adding a new person to a post"
        form["party_identifier"] = self.labour_party.ec_id
        form.submit()

        response = self.app.get(
            self.dulwich_post_ballot.get_absolute_url(), user=self.user
        )
        form = response.forms["new-candidate-form"]
        form["name"] = "Charlotte O'Lucas"  # testers license
        form["tmp_person_identifiers-0-value"] = "charlotte@example.com"
        form["tmp_person_identifiers-0-value_type"] = "email"
        form["source"] = "Testing adding a new person to a post"
        form["party_identifier"] = self.labour_party.ec_id
        form.submit()

        # check searching finds them
        response = self.app.get("/search?q=Elizabeth")
        self.assertTrue(re.search(r"""<a[^>]*>Elizabeth""", response.text))

        self.assertFalse(re.search(r"""<a[^>]*>Mr Darcy""", response.text))

        response = self.app.get(
            self.dulwich_post_ballot.get_absolute_url(), user=self.user
        )
        form = response.forms["new-candidate-form"]
        form["name"] = "Elizabeth Jones"
        form["tmp_person_identifiers-0-value"] = "e.jones@example.com"
        form["tmp_person_identifiers-0-value_type"] = "email"
        form["source"] = "Testing adding a new person to a post"
        form["party_identifier"] = self.labour_party.ec_id
        form.submit()

        response = self.app.get("/search?q=Elizabeth")
        self.assertTrue(
            re.search(r"""<a[^>]*>Elizabeth Bennet""", response.text)
        )
        self.assertTrue(
            re.search(r"""<a[^>]*>Elizabeth Jones""", response.text)
        )

        person = Person.objects.get(name="Elizabeth Jones")
        response = self.app.get(
            "/person/{}/update".format(person.id), user=self.user
        )
        form = response.forms["person-details"]
        form["name"] = "Lizzie Jones"
        form["source"] = "Some source of this information"
        form.submit()

        response = self.app.get("/search?q=Elizabeth")
        self.assertTrue(
            re.search(r"""<a[^>]*>Elizabeth Bennet""", response.text)
        )
        self.assertFalse(
            re.search(r"""<a[^>]*>Elizabeth Jones""", response.text)
        )

        # check that searching for names with apostrophe works
        response = self.app.get("/search?q=O'Lucas")
        self.assertTrue(re.search(r"""<a[^>]*>Charlotte""", response.text))

        # check that searching with middle names works
        response = self.app.get("/search?q=Elizabeth+Mary+Bennet")
        self.assertTrue(
            re.search(r"""<a[^>]*>Elizabeth Bennet""", response.text)
        )

    def test_search_finds_other_names(self):
        person = PersonFactory(name="Henry Jekyll")
        person.other_names.create(name="Edward Hyde")
        person.save()
        qs = search_person_by_name("Edward Hyde")
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().name, "Henry Jekyll")

    def test_name_synonyms(self):
        """
        Make sure "Bertie" doesn't find "Bertram" until we add
        a name synonym asserting that "Bertram" and "Bertie" should
        be considered the same.

        """
        person = PersonFactory(name="Bertram Wilberforce Wooster")
        person.save()
        self.assertFalse(search_person_by_name("Bertie").exists())

        PersonNameSynonym.objects.create(term="bertie", synonym="Bertram")
        self.assertFalse(search_person_by_name("Bertie").exists())
