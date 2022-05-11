from datetime import timedelta

from django.conf import settings
from django.core.files.storage import DefaultStorage
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

import people.tests.factories
from candidates.csv_helpers import list_to_csv, memberships_dicts_for_csv
from candidates.models import PersonRedirect
from candidates.tests.helpers import TmpMediaRootMixin
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME
from people.models import PersonImage
from popolo.models import Membership
from ynr_refactoring.settings import PersonIdentifierFields

from . import factories
from .auth import TestUserMixin
from .dates import FOUR_YEARS_IN_DAYS, date_in_near_future
from .uk_examples import UK2015ExamplesMixin


class CSVTests(TmpMediaRootMixin, TestUserMixin, UK2015ExamplesMixin, TestCase):
    maxDiff = None

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
            gender="female",
        )
        PersonImage.objects.create_from_file(
            filename=EXAMPLE_IMAGE_FILENAME,
            new_filename="images/jowell-pilot.jpg",
            defaults={
                "person": self.gb_person,
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
            identifier="66135",
            label="Member of Parliament for North Antrim",
            party_set=self.ni_parties,
        )
        factories.MembershipFactory.create(
            person=self.ni_person,
            post=north_antrim_post,
            party=self.sinn_fein,
            party_name=self.sinn_fein.name,
            ballot=self.election.ballot_set.get(post=north_antrim_post),
        )
        factories.MembershipFactory.create(
            person=self.ni_person,
            post=north_antrim_post,
            party=self.sinn_fein,
            party_name=self.sinn_fein.name,
            ballot=self.earlier_election.ballot_set.get(post=north_antrim_post),
        )
        factories.MembershipFactory.create(
            person=self.gb_person,
            post=self.camberwell_post,
            party=self.labour_party,
            party_name=self.labour_party.name,
            ballot=self.camberwell_post_ballot,
        )
        factories.MembershipFactory.create(
            person=self.gb_person,
            post=self.dulwich_post,
            party=self.labour_party,
            party_name=self.labour_party.name,
            ballot=self.dulwich_post_ballot_earlier,
        )

        self.gb_person.tmp_person_identifiers.create(
            internal_identifier="uk.org.publicwhip/person/10326",
            value_type="theyworkforyou",
            value="http://www.theyworkforyou.com/mp/10326",
        )
        self.gb_person.tmp_person_identifiers.create(
            value_type="email", value="jowell@example.com"
        )
        self.gb_person.tmp_person_identifiers.create(
            value_type=PersonIdentifierFields.wikidata_id.name, value="Q123456"
        )

    def test_as_single_dict(self):
        membership = (
            Membership.objects.for_csv()
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
        self.assertEqual(len(membership_dict.keys()), 47)
        self.assertEqual(membership_dict["id"], 2009)

        self.assertEqual(
            membership_dict["parlparse_id"], "uk.org.publicwhip/person/10326"
        )
        self.assertEqual(
            membership_dict["theyworkforyou_url"],
            "http://www.theyworkforyou.com/mp/10326",
        )

    def test_as_dict_2010(self):
        with self.assertNumQueries(8):
            memberships_dicts, elected = memberships_dicts_for_csv(
                self.earlier_election.slug
            )
        self.assertEqual(len(memberships_dicts[self.earlier_election.slug]), 2)
        membership_dict = memberships_dicts["parl.2010-05-06"][1]
        self.assertEqual(len(membership_dict.keys()), 47)
        self.assertEqual(membership_dict["id"], 2009)

    def test_csv_output(self):
        tessa_image_url = self.gb_person.image.image.url
        election_date = date_in_near_future
        earlier_election_date = date_in_near_future - timedelta(
            days=FOUR_YEARS_IN_DAYS
        )
        PersonRedirect.objects.create(old_person_id=12, new_person_id=1953)
        PersonRedirect.objects.create(old_person_id=56, new_person_id=1953)
        example_output = (
            "id,name,election,ballot_paper_id,election_date,seats_contested,party_id,party_name,party_description_text,previous_party_affiliations,post_id,post_label,organisation_name,NUTS1,honorific_prefix,honorific_suffix,gender,birth_date,elected,email,twitter_username,facebook_page_url,party_ppc_page_url,facebook_personal_url,homepage_url,wikipedia_url,linkedin_url,image_url,proxy_image_url_template,image_copyright,image_uploading_user,image_uploading_user_notes,twitter_user_id,election_current,party_lists_in_use,party_list_position,old_person_ids,gss_code,parlparse_id,theyworkforyou_url,party_ec_id,favourite_biscuits,cancelled_poll,wikidata_id,blog_url,instagram_url,youtube_profile\r\n"
            + f"1953,Daithí McKay,parl.2010-05-06,parl.66135.2010-05-06,{earlier_election_date},1,party:39,Sinn Féin,,,66135,North Antrim,House of Commons,,,,male,,,,,,,,,,,,,,,,,False,False,,12;56,,,,PP39,,False,,,,\r\n"
            + f"2009,Tessa Jowell,parl.2010-05-06,parl.65808.2010-05-06,{earlier_election_date},1,party:53,Labour Party,,,65808,Dulwich and West Norwood,House of Commons,,Ms,DBE,female,,,jowell@example.com,,,,,,,,{tessa_image_url},,example-license,john,A photo of Tessa Jowell,,False,False,,,,uk.org.publicwhip/person/10326,http://www.theyworkforyou.com/mp/10326,PP53,,False,Q123456,,,\r\n"
            + f"1953,Daithí McKay,parl.2015-05-07,parl.66135.2015-05-07,{election_date},1,party:39,Sinn Féin,,,66135,North Antrim,House of Commons,,,,male,,,,,,,,,,,,,,,,,True,False,,12;56,,,,PP39,,False,,,,\r\n"
            + f"2009,Tessa Jowell,parl.2015-05-07,parl.65913.2015-05-07,{election_date},1,party:53,Labour Party,,,65913,Camberwell and Peckham,House of Commons,,Ms,DBE,female,,,jowell@example.com,,,,,,,,{tessa_image_url},,example-license,john,A photo of Tessa Jowell,,True,False,,,,uk.org.publicwhip/person/10326,http://www.theyworkforyou.com/mp/10326,PP53,,False,Q123456,,,\r\n"
        )

        with self.assertNumQueries(14):
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
            set(sorted(self.storage.listdir(".")[1])),
            set(
                [
                    "candidates-parl.2010-05-06.csv",
                    "candidates-parl.2015-05-07.csv",
                    "candidates-all.csv",
                    "candidates-elected-all.csv",
                    "candidates-local.maidstone.2016-05-05.csv",
                    "candidates-2015-05-07.csv",
                    "candidates-2010-05-06.csv",
                    "candidates-senedd.c.2021-05-06.csv",
                ]
            ),
        )

    def test_create_csv_management_command_single_election(self):
        # An empty media directory
        self.assertEqual(
            self.storage.listdir(self.storage.base_location), (["images"], [])
        )

        # We expect a single CSV file
        call_command("candidates_create_csv", "--election", "parl.2015-05-07")
        self.assertSetEqual(
            set(self.storage.listdir(".")[1]),
            set(
                ["candidates-parl.2015-05-07.csv", "candidates-2015-05-07.csv"]
            ),
        )

    def test_create_csv_management_command_single_election_doesnt_exist(self):
        # An empty media directory, apart from the images dir
        self.assertEqual(
            self.storage.listdir(self.storage.base_location), (["images"], [])
        )

        with self.assertRaises(CommandError):
            call_command("candidates_create_csv", "--election", "foo")

    def test_create_csv_no_candidates_for_election(self):
        # An empty media directory, apart from the images dir
        self.assertEqual(
            self.storage.listdir(self.storage.base_location), (["images"], [])
        )

        factories.ElectionFactory.create(
            slug="2018", name="2018 General Election", organization=self.commons
        )

        call_command("candidates_create_csv")
        self.assertSetEqual(
            set(self.storage.listdir(".")[1]),
            set(
                [
                    "candidates-parl.2010-05-06.csv",
                    "candidates-parl.2015-05-07.csv",
                    "candidates-2018.csv",
                    "candidates-all.csv",
                    "candidates-elected-all.csv",
                    "candidates-local.maidstone.2016-05-05.csv",
                    "candidates-2015-05-07.csv",
                    "candidates-2010-05-06.csv",
                    "candidates-senedd.c.2021-05-06.csv",
                ]
            ),
        )
        empty_file = self.storage.open("candidates-2018.csv").read()
        self.assertEqual(len(empty_file.splitlines()), 1)
        self.assertEqual(
            empty_file.splitlines()[0].decode(),
            (",".join(settings.CSV_ROW_FIELDS)),
        )

        non_empty_file = self.storage.open(
            "candidates-parl.2015-05-07.csv"
        ).read()
        self.assertEqual(len(non_empty_file.splitlines()), 3)

    def test_previous_party_affiliations_string(self):

        for membership in Membership.objects.all():
            with self.subTest(msg=membership):
                self.assertEqual(
                    membership.previous_party_affiliations_string, ""
                )

        # welsh run ballot
        welsh_candidacy = factories.MembershipFactory.create(
            person=people.tests.factories.PersonFactory.create(),
            post=self.welsh_run_post,
            party=self.labour_party,
            party_name=self.labour_party.name,
            ballot=self.senedd_ballot,
        )
        welsh_candidacy.previous_party_affiliations.add(self.conservative_party)
        welsh_candidacy.previous_party_affiliations.add(self.ld_party)
        welsh_candidacy.previous_party_affiliations.add(self.green_party)
        expected = f"{self.conservative_party.ec_id}; {self.green_party.ec_id}; {self.ld_party.ec_id}"
        self.assertEqual(
            welsh_candidacy.previous_party_affiliations_string, expected
        )
