from datetime import timedelta

from django.conf import settings
from django.test import TestCase
from django.core.files.storage import DefaultStorage
from django.core.management import call_command
from django.core.management.base import CommandError

import people.tests.factories
from people.models import PersonImage
from candidates.models import PersonRedirect
from candidates.csv_helpers import list_to_csv, memberships_dicts_for_csv
from candidates.tests.helpers import TmpMediaRootMixin
from popolo.models import Membership

from . import factories
from .auth import TestUserMixin
from .dates import date_in_near_future, FOUR_YEARS_IN_DAYS
from .uk_examples import UK2015ExamplesMixin
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME


class CSVTests(TmpMediaRootMixin, TestUserMixin, UK2015ExamplesMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.storage = DefaultStorage()
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
        PersonImage.objects.create_from_file(
            EXAMPLE_IMAGE_FILENAME,
            "images/jowell-pilot.jpg",
            defaults={
                "person": self.gb_person,
                "is_primary": True,
                "source": "Taken from Wikipedia",
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "A photo of Tessa Jowell",
            },
        )

        self.ni_person = people.tests.factories.PersonFactory.create(
            id=1953, name="Daithí McKay", gender="male"
        )
        north_antrim_post = factories.PostFactory.create(
            elections=(self.election, self.earlier_election),
            organization=self.commons,
            slug="66135",
            label="Member of Parliament for North Antrim",
            party_set=self.ni_parties,
        )
        factories.MembershipFactory.create(
            person=self.ni_person,
            post=north_antrim_post,
            party=self.sinn_fein,
            post_election=self.election.postextraelection_set.get(
                post=north_antrim_post
            ),
        )
        factories.MembershipFactory.create(
            person=self.ni_person,
            post=north_antrim_post,
            party=self.sinn_fein,
            post_election=self.earlier_election.postextraelection_set.get(
                post=north_antrim_post
            ),
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
            post_election=self.dulwich_post_pee_earlier,
        )
        self.gb_person.identifiers.create(
            identifier="uk.org.publicwhip/person/10326",
            scheme="uk.org.publicwhip",
        )

    def test_as_single_dict(self):
        membership = (
            Membership.objects.joins_for_csv()
            .filter(person=self.gb_person.id)
            .first()
        )
        # After the select_related and prefetch_related calls
        # PersonExtra there should only be one more query - that to
        # find the complex fields mapping:
        with self.assertNumQueries(0):
            membership_dict = membership.dict_for_csv()

        self.assertEqual(
            sorted(list(membership_dict.keys())),
            sorted(settings.CSV_ROW_FIELDS),
        )
        self.assertEqual(len(membership_dict.keys()), 38)
        self.assertEqual(membership_dict["id"], 2009)

        self.assertEqual(
            membership_dict["parlparse_id"], "uk.org.publicwhip/person/10326"
        )
        self.assertEqual(
            membership_dict["theyworkforyou_url"],
            "http://www.theyworkforyou.com/mp/10326",
        )

    def test_as_dict_2010(self):
        with self.assertNumQueries(7):
            memberships_dicts, elected = memberships_dicts_for_csv(
                self.earlier_election.slug
            )
        self.assertEqual(len(memberships_dicts[self.earlier_election.slug]), 2)
        membership_dict = memberships_dicts["2010"][0]
        self.assertEqual(len(membership_dict.keys()), 38)
        self.assertEqual(membership_dict["id"], 2009)

    def test_csv_output(self):
        tessa_image_url = self.gb_person.primary_image.url
        d = {
            "election_date": date_in_near_future,
            "earlier_election_date": date_in_near_future
            - timedelta(days=FOUR_YEARS_IN_DAYS),
        }
        PersonRedirect.objects.create(old_person_id=12, new_person_id=1953)
        PersonRedirect.objects.create(old_person_id=56, new_person_id=1953)
        self.maxDiff = None
        example_output = (
            "id,name,honorific_prefix,honorific_suffix,gender,birth_date,election,party_id,party_name,post_id,post_label,mapit_url,elected,email,twitter_username,facebook_page_url,party_ppc_page_url,facebook_personal_url,homepage_url,wikipedia_url,linkedin_url,image_url,proxy_image_url_template,image_copyright,image_uploading_user,image_uploading_user_notes,twitter_user_id,election_date,election_current,party_lists_in_use,party_list_position,old_person_ids,gss_code,parlparse_id,theyworkforyou_url,party_ec_id,favourite_biscuits,cancelled_poll\r\n"
            + "1953,Daith\xed McKay,,,male,,2010,party:39,Sinn F\xe9in,66135,North Antrim,,,,,,,,,,,,,,,,,{earlier_election_date},False,False,,12;56,,,,PP39,,False\r\n".format(
                **d
            )
            + "2009,Tessa Jowell,Ms,DBE,female,,2010,party:53,Labour Party,65808,Dulwich and West Norwood,,,jowell@example.com,,,,,,,,{image_url},,example-license,john,A photo of Tessa Jowell,,{earlier_election_date},False,False,,,,uk.org.publicwhip/person/10326,http://www.theyworkforyou.com/mp/10326,PP53,,False\r\n".format(
                image_url=tessa_image_url, **d
            )
            + "1953,Daith\xed McKay,,,male,,2015,party:39,Sinn F\xe9in,66135,North Antrim,,,,,,,,,,,,,,,,,{election_date},True,False,,12;56,,,,PP39,,False\r\n".format(
                **d
            )
            + "2009,Tessa Jowell,Ms,DBE,female,,2015,party:53,Labour Party,65913,Camberwell and Peckham,,,jowell@example.com,,,,,,,,{image_url},,example-license,john,A photo of Tessa Jowell,,{election_date},True,False,,,,uk.org.publicwhip/person/10326,http://www.theyworkforyou.com/mp/10326,PP53,,False\r\n".format(
                image_url=tessa_image_url, **d
            )
        )

        with self.assertNumQueries(7):
            memberships_dicts, elected = memberships_dicts_for_csv()
        all_members = []
        for slug, members in memberships_dicts.items():
            all_members += members
        self.assertEqual(list_to_csv(all_members), example_output)

    def test_create_csv_management_command(self):
        # An empty media directory
        self.assertEqual(
            self.storage.listdir(self.storage.base_location)[1], []
        )

        # We expect a CSV file per election, and one for all elections
        call_command("candidates_create_csv")
        self.assertEqual(
            sorted(self.storage.listdir(self.storage.base_location)[1]),
            [
                "candidates-2010.csv",
                "candidates-2015.csv",
                "candidates-all.csv",
                "candidates-elected-all.csv",
            ],
        )

    def test_create_csv_management_command_single_election(self):
        # An empty media directory
        self.assertEqual(
            self.storage.listdir(self.storage.base_location), (["images"], [])
        )

        # We expect a single CSV file
        call_command("candidates_create_csv", "--election", "2015")
        self.assertEqual(
            self.storage.listdir(self.storage.base_location)[1],
            ["candidates-2015.csv"],
        )

    def test_create_csv_management_command_single_election_doesnt_exist(self):
        # An empty media directory, apart from the images dir
        self.assertEqual(
            self.storage.listdir(self.storage.base_location), (["images"], [])
        )

        with self.assertRaises(CommandError):
            call_command("candidates_create_csv", "--election", "foo")
