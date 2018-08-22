from datetime import timedelta
from os.path import join

from django.conf import settings
from django.test import TestCase

from candidates.models import ImageExtra, PersonRedirect
from candidates.csv_helpers import list_to_csv
from popolo.models import Person

from . import factories
from .auth import TestUserMixin
from .dates import date_in_near_future, FOUR_YEARS_IN_DAYS
from .uk_examples import UK2015ExamplesMixin
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME


def get_person_with_joins(person_id):
    return Person.objects.joins_for_csv_output().get(pk=person_id)


class CSVTests(TestUserMixin, UK2015ExamplesMixin, TestCase):
    def setUp(self):
        super().setUp()
        # The second person's name (and party name) have diacritics in
        # them to test handling of Unicode when outputting to CSV.
        self.gb_person = factories.PersonFactory.create(
            id=2009,
            name="Tessa Jowell",
            honorific_suffix="DBE",
            honorific_prefix="Ms",
            email="jowell@example.com",
            gender="female",
        )
        ImageExtra.objects.create_from_file(
            EXAMPLE_IMAGE_FILENAME,
            "images/jowell-pilot.jpg",
            base_kwargs={
                "content_object": self.gb_person,
                "is_primary": True,
                "source": "Taken from Wikipedia",
            },
            extra_kwargs={
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "A photo of Tessa Jowell",
            },
        )

        self.ni_person = factories.PersonFactory.create(
            id=1953, name="Daithí McKay", gender="male"
        )
        north_antrim_post_extra = factories.PostExtraFactory.create(
            elections=(self.election, self.earlier_election),
            base__organization=self.commons,
            slug="66135",
            base__label="Member of Parliament for North Antrim",
            party_set=self.ni_parties,
        )
        factories.MembershipFactory.create(
            person=self.ni_person,
            post=north_antrim_post_extra.base,
            on_behalf_of=self.sinn_fein_extra.base,
            post_election=self.election.postextraelection_set.get(
                postextra=north_antrim_post_extra
            ),
        )
        factories.MembershipFactory.create(
            person=self.ni_person,
            post=north_antrim_post_extra.base,
            on_behalf_of=self.sinn_fein_extra.base,
            post_election=self.earlier_election.postextraelection_set.get(
                postextra=north_antrim_post_extra
            ),
        )
        factories.MembershipFactory.create(
            person=self.gb_person,
            post=self.camberwell_post_extra.base,
            on_behalf_of=self.labour_party_extra.base,
            post_election=self.camberwell_post_extra_pee,
        )
        factories.MembershipFactory.create(
            person=self.gb_person,
            post=self.dulwich_post_extra.base,
            on_behalf_of=self.labour_party_extra.base,
            post_election=self.dulwich_post_extra_pee_earlier,
        )

    def test_as_list_single_dict(self):
        person = get_person_with_joins(self.gb_person.id)
        # After the select_related and prefetch_related calls
        # PersonExtra there should only be one more query - that to
        # find the complex fields mapping:
        with self.assertNumQueries(0):
            person_dict_list = person.as_list_of_dicts(self.election)
        self.assertEqual(len(person_dict_list), 1)
        person_dict = person_dict_list[0]
        self.assertEqual(len(person_dict), 37)
        self.assertEqual(person_dict["id"], 2009)

    def test_as_dict_2010(self):
        person = get_person_with_joins(self.gb_person.id)
        # After the select_related and prefetch_related calls
        # PersonExtra there should only be one more query - that to
        # find the complex fields mapping:
        with self.assertNumQueries(0):
            person_dict_list = person.as_list_of_dicts(self.earlier_election)
        self.assertEqual(len(person_dict_list), 1)
        person_dict = person_dict_list[0]
        self.assertEqual(len(person_dict), 37)
        self.assertEqual(person_dict["id"], 2009)

    def test_csv_output(self):
        tessa_image_url = self.gb_person.primary_image().url
        d = {
            "election_date": date_in_near_future,
            "earlier_election_date": date_in_near_future
            - timedelta(days=FOUR_YEARS_IN_DAYS),
        }
        PersonRedirect.objects.create(old_person_id=12, new_person_id=1953)
        PersonRedirect.objects.create(old_person_id=56, new_person_id=1953)
        self.maxDiff = None
        example_output = "id,name,honorific_prefix,honorific_suffix,gender,birth_date,election,party_id,party_name,post_id,post_label,mapit_url,elected,email,twitter_username,facebook_page_url,party_ppc_page_url,facebook_personal_url,homepage_url,wikipedia_url,linkedin_url,image_url,proxy_image_url_template,image_copyright,image_uploading_user,image_uploading_user_notes,twitter_user_id,election_date,election_current,party_lists_in_use,party_list_position,old_person_ids,gss_code,parlparse_id,theyworkforyou_url,party_ec_id,favourite_biscuits\r\n" "2009,Tessa Jowell,Ms,DBE,female,,2015,party:53,Labour Party,65913,Camberwell and Peckham,,,jowell@example.com,,,,,,,,{image_url},,example-license,john,A photo of Tessa Jowell,,{election_date},True,False,,,,,,,\r\n".format(
            image_url=tessa_image_url, **d
        ) + "2009,Tessa Jowell,Ms,DBE,female,,2010,party:53,Labour Party,65808,Dulwich and West Norwood,,,jowell@example.com,,,,,,,,{image_url},,example-license,john,A photo of Tessa Jowell,,{earlier_election_date},False,False,,,,,,,\r\n".format(
            image_url=tessa_image_url, **d
        ) + "1953,Daith\xed McKay,,,male,,2015,party:39,Sinn F\xe9in,66135,North Antrim,,,,,,,,,,,,,,,,,{election_date},True,False,,12;56,,,,,\r\n".format(
            **d
        ) + "1953,Daith\xed McKay,,,male,,2010,party:39,Sinn F\xe9in,66135,North Antrim,,,,,,,,,,,,,,,,,{earlier_election_date},False,False,,12;56,,,,,\r\n".format(
            **d
        )
        gb_person = get_person_with_joins(self.gb_person.id)
        ni_person = get_person_with_joins(self.ni_person.id)
        # After the select_related and prefetch_related calls on
        # PersonExtra, there should only be one query per PersonExtra:
        redirects = PersonRedirect.all_redirects_dict()
        with self.assertNumQueries(0):
            list_of_dicts = gb_person.as_list_of_dicts(
                None, redirects=redirects
            )
            list_of_dicts += ni_person.as_list_of_dicts(
                None, redirects=redirects
            )
        self.assertEqual(list_to_csv(list_of_dicts), example_output)
