import codecs
from io import BytesIO
from mock import patch
import os

from datetime import datetime, timedelta

from django_webtest import WebTest
from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.utils.timezone import make_aware

from lxml import etree

import people.tests.factories
from candidates.models import LoggedAction
from candidates.tests.uk_examples import UK2015ExamplesMixin

from people.models import Person
from parties.models import Party

from . import factories
from .auth import TestUserMixin
from people.tests.test_version_diffs import tidy_html_whitespace


def random_person_id():
    return codecs.encode(os.urandom(8), "hex").decode()


def change_updated_and_created(la, timestamp):
    # auto_add_now and auto_now are used for the LoggedAction created
    # and updated fields, which are awkward to override. You can do
    # this, however, by use the update() method of QuerySet, which is
    # converted directly to an SQL UPDATE and doesn't trigger
    # save-related signals.
    LoggedAction.objects.filter(pk=la.pk).update(
        created=timestamp, updated=timestamp
    )


def canonicalize_xml(xml_bytes):
    parsed = etree.fromstring(xml_bytes)
    out = BytesIO()
    parsed.getroottree().write_c14n(out)
    return out.getvalue()


def fake_diff_html(self, version_id, inline_style=False):
    return "<div{}>Fake diff</div>".format(
        ' style="color: red"' if inline_style else ""
    )


class TestFlaggedEdits(UK2015ExamplesMixin, TestUserMixin, WebTest):
    def test_needs_review_due_to_first_edits(self):
        self.assertFalse(LoggedAction.objects.needs_review().exists())

        example_person = people.tests.factories.PersonFactory.create(
            id="2009", name="Tessa Jowell"
        )

        for i in range(20):
            LoggedAction.objects.create(
                id=(1000 + i),
                user=self.user,
                action_type="person-update",
                person=example_person,
                popit_person_new_version=random_person_id(),
                source="Just for tests...",
            )

        self.assertEqual(LoggedAction.objects.all().count(), 20)
        self.assertEqual(
            LoggedAction.objects.needs_review().count(),
            settings.NEEDS_REVIEW_FIRST_EDITS,
        )

    def test_needs_review_due_to_candidate_having_died(self):
        self.assertFalse(LoggedAction.objects.needs_review().exists())

        example_person = people.tests.factories.PersonFactory.create(
            id="2009", name="Tessa Jowell", death_date="2018-01-01"
        )

        LoggedAction.objects.create(
            id=(1000),
            user=self.user,
            action_type="person-update",
            person=example_person,
            popit_person_new_version=random_person_id(),
            source="Just for tests...",
        )

        self.assertEqual(LoggedAction.objects.all().count(), 1)
        self.assertEqual(
            LoggedAction.objects.needs_review().get().flagged_reason,
            "Edit of a candidate who has died",
        )
        self.assertEqual(
            LoggedAction.objects.needs_review().get().flagged_type,
            "needs_review_due_to_candidate_having_died",
        )

    @override_settings(PEOPLE_LIABLE_TO_VANDALISM={2009})
    def test_needs_review_due_to_high_profile(self):
        self.assertFalse(LoggedAction.objects.needs_review().exists())

        example_person = people.tests.factories.PersonFactory.create(
            id="2009", name="Tessa Jowell", death_date="2018-01-01"
        )

        LoggedAction.objects.create(
            id=(1000),
            user=self.user,
            action_type="person-update",
            person=example_person,
            popit_person_new_version=random_person_id(),
            source="Just for tests...",
        )

        self.assertEqual(LoggedAction.objects.all().count(), 1)
        self.assertEqual(
            LoggedAction.objects.needs_review().get().flagged_reason,
            "Edit of a candidate whose record may be particularly liable to vandalism",
        )
        self.assertEqual(
            LoggedAction.objects.needs_review().get().flagged_type,
            "needs_review_due_to_high_profile",
        )


@patch.object(Person, "diff_for_version", fake_diff_html)
@patch("candidates.models.db.datetime")
@override_settings(PEOPLE_LIABLE_TO_VANDALISM={2811})
class TestNeedsReviewFeed(UK2015ExamplesMixin, TestUserMixin, WebTest):

    maxDiff = None
    csrf_checks = False

    def setUp(self):
        super().setUp()
        self.current_datetime = make_aware(datetime(2017, 5, 2, 18, 10, 5, 0))
        # Reuse existing users created in TestUserMixin:
        for username, u in (
            ("lapsed_experienced", self.user),
            ("new_suddenly_lots", self.user_who_can_merge),
            ("new_only_one", self.user_who_can_upload_documents),
            ("morbid_vandal", self.user_who_can_lock),
        ):
            u.username = username
            u.save()
            setattr(self, username, u)

        example_person = people.tests.factories.PersonFactory.create(
            id="2009", name="Tessa Jowell"
        )

        # Create old edits for the experienced user:
        date_ages_ago = self.current_datetime - timedelta(days=365)
        for i in range(20):
            la = LoggedAction.objects.create(
                id=(1000 + i),
                user=self.lapsed_experienced,
                action_type="person-update",
                person=example_person,
                popit_person_new_version=random_person_id(),
                source="Just for tests...",
            )
            dt = date_ages_ago - timedelta(minutes=i * 10)
            change_updated_and_created(la, dt)
        # ... and a couple of new edits for the experienced user:
        for i in range(2):
            la = LoggedAction.objects.create(
                id=(1500 + i),
                user=self.lapsed_experienced,
                action_type="person-update",
                person=example_person,
                popit_person_new_version=random_person_id(),
                source="Just for tests...",
            )
            dt = self.current_datetime - timedelta(minutes=i * 5)
            change_updated_and_created(la, dt)

        # Create lots of very recent edits for a new user:
        for i in range(10):
            la = LoggedAction.objects.create(
                id=(2000 + i),
                user=self.new_suddenly_lots,
                action_type="person-update",
                person=example_person,
                popit_person_new_version=random_person_id(),
                source="Just for tests",
            )
            dt = self.current_datetime - timedelta(minutes=i * 7)
            change_updated_and_created(la, dt)

        # Create a single recent edit for a new user:
        la = LoggedAction.objects.create(
            id=(2500 + i),
            user=self.new_only_one,
            action_type="person-update",
            person=example_person,
            popit_person_new_version=random_person_id(),
            source="Just for tests",
        )
        dt = self.current_datetime - timedelta(minutes=2)
        change_updated_and_created(la, dt)

        # Create a candidate with a death date, and edit of that
        # candidate:
        dead_person = people.tests.factories.PersonFactory.create(
            id="7448",
            name="The Eurovisionary Ronnie Carroll",
            birth_date="1934-08-18",
            death_date="2015-04-13",
        )
        la = LoggedAction.objects.create(
            id=3000,
            user=self.morbid_vandal,
            action_type="person-update",
            person=dead_person,
            popit_person_new_version=random_person_id(),
            source="Just for tests",
            updated=dt,
            created=dt,
        )
        dt = self.current_datetime - timedelta(minutes=4)
        change_updated_and_created(la, dt)

        prime_minister = people.tests.factories.PersonFactory.create(
            id=2811, name="Theresa May"
        )
        # Create a candidate on the "liable to vandalism" list.
        la = LoggedAction.objects.create(
            id=4000,
            user=self.lapsed_experienced,
            action_type="person-update",
            person=prime_minister,
            popit_person_new_version=random_person_id(),
            source="Just for tests...",
        )
        dt = self.current_datetime - timedelta(minutes=3)
        change_updated_and_created(la, dt)

        # Create a photo-upload action - this should not be included:
        la = LoggedAction.objects.create(
            id=4500,
            user=self.lapsed_experienced,
            action_type="photo-upload",
            person=example_person,
            popit_person_new_version=random_person_id(),
            source="Just for tests...",
        )
        dt = self.current_datetime - timedelta(minutes=41)
        change_updated_and_created(la, dt)

        # Let's say a new user is has locked a constituency - this is
        # a useful test because (because of a bug) locked
        # constituencies have neither a post nor a person set:
        la = LoggedAction.objects.create(
            id=5000,
            user=self.morbid_vandal,
            action_type="constituency-lock",
            person=None,
            post=None,
            popit_person_new_version="",
            source="Testing no post and no person",
        )
        dt = self.current_datetime - timedelta(minutes=13)
        change_updated_and_created(la, dt)

        resp = self.app.get(
            self.dulwich_post_ballot.get_absolute_url(), user=self.user
        )

        form = resp.forms["new-candidate-form"]

        form["name"] = "Yoshi Aarle"
        form["source"] = "just a test"
        form["standing_parl.2015-05-07"] = "standing"
        form["constituency_parl.2015-05-07"] = "65808"
        form["party_GB_parl.2015-05-07"] = str(Party.objects.first().ec_id)
        response = form.submit().follow()

        person = response.context["person"]
        self.person = person

        response = self.app.get(
            "/person/{}/update/".format(person.pk), user=self.user
        )

        form = response.forms[1]

        form[
            "biography"
        ] = """
                Now, this is a story all about how
                my life got flipped-turned upside down"""
        form["source"] = "just a test"
        form.submit()

        las = LoggedAction.objects.filter(person=person)
        dt = self.current_datetime - timedelta(minutes=40)
        for la in las:
            change_updated_and_created(la, dt)
            if la.action_type == "person-update":
                self.la_id = la.pk

    def test_needs_review_as_expected(self, mock_datetime):
        self.maxDiff = None
        mock_datetime.now.return_value = self.current_datetime
        needs_review_qs = (
            LoggedAction.objects.in_recent_days(5)
            .needs_review()
            .order_by("-created")
        )
        # Here we're expecting the following LoggedActions to be picked out:
        #    1 edit of a dead candidate (by 'morbid_vandal')
        #    3 edits from 'new_suddenly_lots' (we just consider the first
        #      three edits from a new user needs_review)
        #    1 first edit from 'new_only_one'
        #    1 edit from a user who was mostly active in the past to the
        #      prime minister's record
        #    1 constituency-lock from a new user
        #    (TMP REMOVED) 1 edit of a biography field
        self.assertEqual(needs_review_qs.count(), 1 + 3 + 1 + 1 + 1)
        results = [
            (la.user.username, la.action_type, la.flagged_reason)
            for la in needs_review_qs
        ]

        self.assertEqual(
            results,
            [
                (
                    "new_suddenly_lots",
                    "person-update",
                    "One of the first 3 edits of user new_suddenly_lots",
                ),
                (
                    "new_only_one",
                    "person-update",
                    "One of the first 3 edits of user new_only_one",
                ),
                (
                    "lapsed_experienced",
                    "person-update",
                    "Edit of a candidate whose record may be particularly liable to vandalism",
                ),
                (
                    "morbid_vandal",
                    "person-update",
                    "Edit of a candidate who has died",
                ),
                (
                    "new_suddenly_lots",
                    "person-update",
                    "One of the first 3 edits of user new_suddenly_lots",
                ),
                # (
                #     "lapsed_experienced",
                #     "person-update",
                #     ["Edit of a statement to voters"],
                # ),
                (
                    "morbid_vandal",
                    "constituency-lock",
                    "One of the first 3 edits of user morbid_vandal",
                ),
                (
                    "new_suddenly_lots",
                    "person-update",
                    "One of the first 3 edits of user new_suddenly_lots",
                ),
            ],
        )

    def test_xml_feed(self, mock_datetime):
        mock_datetime.now.return_value = self.current_datetime
        response = self.app.get("/feeds/needs-review.xml")
        got = canonicalize_xml(response.content)

        print(got)

        self.maxDiff = None

        expected = (
            b'<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-gb"><title>example.co'
            b'm changes for review</title><link href="http://example.com/feeds/needs-revie'
            b'w.xml" rel="alternate"></link><link href="http://example.com/feeds/needs-rev'
            b'iew.xml" rel="self"></link><id>http://example.com/feeds/needs-review.xml</id'
            b"><updated>2017-05-02T17:10:05+00:00</updated><entry><title>Tessa Jowell (200"
            b'9) - person-update</title><link href="http://example.com/person/2009" rel="a'
            b'lternate"></link><updated>2017-05-02T17:10:05+00:00</updated><author><name>n'
            b'ew_suddenly_lots</name></author><id>needs-review:2000</id><summary type="htm'
            b'l">&lt;p&gt;person-update of &lt;a href="/person/2009"&gt;Tessa Jowell (2009'
            b")&lt;/a&gt; by new_suddenly_lots with source: \xe2\x80\x9c Just for tests"
            b" \xe2\x80\x9d;&lt;/p&gt;\n&lt;ul&gt;\nOne of the first 3 edits of user new_"
            b'suddenly_lots\n&lt;/ul&gt;&lt;/p&gt;&lt;div style="color: red"&gt;Fake di'
            b"ff&lt;/div&gt;</summary></entry><entry><title>Tessa Jowell (2009) - person-u"
            b'pdate</title><link href="http://example.com/person/2009" rel="alternate"></l'
            b"ink><updated>2017-05-02T17:08:05+00:00</updated><author><name>new_only_one</"
            b'name></author><id>needs-review:2509</id><summary type="html">&lt;p&gt;person'
            b'-update of &lt;a href="/person/2009"&gt;Tessa Jowell (2009)&lt;/a&gt; by new'
            b"_only_one with source: \xe2\x80\x9c Just for tests \xe2\x80\x9d;&lt;/p&gt;"
            b"\n&lt;ul&gt;\nOne of the first 3 edits of user new_only_one\n&lt;/ul&gt;&lt"
            b';/p&gt;&lt;div style="color: red"&gt;Fake diff&lt;/div&gt;</summary></entry>'
            b'<entry><title>Theresa May (2811) - person-update</title><link href="http://e'
            b'xample.com/person/2811" rel="alternate"></link><updated>2017-05-02T17:07:05+'
            b"00:00</updated><author><name>lapsed_experienced</name></author><id>needs-rev"
            b'iew:4000</id><summary type="html">&lt;p&gt;person-update of &lt;a href="/per'
            b'son/2811"&gt;Theresa May (2811)&lt;/a&gt; by lapsed_experienced with source:'
            b" \xe2\x80\x9c Just for tests... \xe2\x80\x9d;&lt;/p&gt;\n&lt;ul&gt;\nEdit of"
            b" a candidate whose record may be particularly liable to vandalism\n&lt;/u"
            b'l&gt;&lt;/p&gt;&lt;div style="color: red"&gt;Fake diff&lt;/div&gt;</summary>'
            b"</entry><entry><title>The Eurovisionary Ronnie Carroll (7448) - person-updat"
            b'e</title><link href="http://example.com/person/7448" rel="alternate"></link>'
            b"<updated>2017-05-02T17:06:05+00:00</updated><author><name>morbid_vandal</nam"
            b'e></author><id>needs-review:3000</id><summary type="html">&lt;p&gt;person-up'
            b'date of &lt;a href="/person/7448"&gt;The Eurovisionary Ronnie Carroll (7448)'
            b"&lt;/a&gt; by morbid_vandal with source: \xe2\x80\x9c Just for tests "
            b"\xe2\x80\x9d;&lt;/p&gt;\n&lt;ul&gt;\nEdit of a candidate who has died\n&lt;/"
            b'ul&gt;&lt;/p&gt;&lt;div style="color: red"&gt;Fake diff&lt;/div&gt;</summary'
            b"></entry><entry><title>Tessa Jowell (2009) - person-update</title><link href"
            b'="http://example.com/person/2009" rel="alternate"></link><updated>2017-05-02'
            b"T17:03:05+00:00</updated><author><name>new_suddenly_lots</name></author><id>"
            b'needs-review:2001</id><summary type="html">&lt;p&gt;person-update of &lt;a h'
            b'ref="/person/2009"&gt;Tessa Jowell (2009)&lt;/a&gt; by new_suddenly_lots wit'
            b"h source: \xe2\x80\x9c Just for tests \xe2\x80\x9d;&lt;/p&gt;\n&lt;ul&gt;\nO"
            b"ne of the first 3 edits of user new_suddenly_lots\n&lt;/ul&gt;&lt;/p&gt;&"
            b'lt;div style="color: red"&gt;Fake diff&lt;/div&gt;</summary></entry><entry><'
            b'title>constituency-lock</title><link href="http://example.com/" rel="alterna'
            b'te"></link><updated>2017-05-02T16:57:05+00:00</updated><author><name>morbid_'
            b'vandal</name></author><id>needs-review:5000</id><summary type="html">&lt;p&g'
            b"t;constituency-lock of  by morbid_vandal with source: \xe2\x80\x9c Testin"
            b"g no post and no person \xe2\x80\x9d;&lt;/p&gt;\n&lt;ul&gt;\nOne of the fir"
            b"st 3 edits of user morbid_vandal\n&lt;/ul&gt;&lt;/p&gt;</summary></entry>"
            b'<entry><title>Tessa Jowell (2009) - person-update</title><link href="http://'
            b'example.com/person/2009" rel="alternate"></link><updated>2017-05-02T16:56:05'
            b"+00:00</updated><author><name>new_suddenly_lots</name></author><id>needs-rev"
            b'iew:2002</id><summary type="html">&lt;p&gt;person-update of &lt;a href="/per'
            b'son/2009"&gt;Tessa Jowell (2009)&lt;/a&gt; by new_suddenly_lots with source:'
            b" \xe2\x80\x9c Just for tests \xe2\x80\x9d;&lt;/p&gt;\n&lt;ul&gt;\nOne of the"
            b" first 3 edits of user new_suddenly_lots\n&lt;/ul&gt;&lt;/p&gt;&lt;div st"
            b'yle="color: red"&gt;Fake diff&lt;/div&gt;</summary></entry></feed>'
        )

        expected = expected.replace(
            b"**YoshiAarleID**", str(self.person.pk).encode()
        )
        expected = expected.replace(b"**laID**", str(self.la_id).encode())
        self.assertEqual(got, expected)


class TestDiffHTML(TestCase):
    def test_missing_version(self):
        person = people.tests.factories.PersonFactory.create(
            name="John Smith", id="1234567", versions="[]"
        )
        la = LoggedAction.objects.create(
            person=person, popit_person_new_version="1376abcd9234"
        )
        self.assertEqual(
            la.diff_html,
            "<p>Couldn&#39;t find version 1376abcd9234 for person with ID "
            "1234567</p>",
        )

    def test_found_version(self):
        person = people.tests.factories.PersonFactory.create(
            name="Sarah Jones",
            id="1234567",
            versions="""[{
                "data": {
                    "honorific_prefix": "Mrs",
                    "honorific_suffix": "",
                    "id": "6704",
                    "identifiers": [],
                    "image": null,
                    "linkedin_url": "",
                    "name": "Sarah Jones",
                    "party_ppc_page_url": "",
                    "proxy_image": null,
                    "twitter_username": "",
                    "wikipedia_url": ""
                },
                "information_source": "Made up 2",
                "timestamp": "2015-05-08T01:52:27.061038",
                "username": "test",
                "version_id": "3fc494d54f61a157"
            },
            {
                "data": {
                    "email": "sarah@example.com",
                    "honorific_prefix": "Mrs",
                    "honorific_suffix": "",
                    "id": "6704",
                    "identifiers": [],
                    "image": null,
                    "linkedin_url": "",
                    "name": "Sarah Jones",
                    "party_ppc_page_url": "",
                    "proxy_image": null,
                    "twitter_username": "",
                    "wikipedia_url": ""
                },
                "information_source": "Made up 1",
                "timestamp": "2015-03-10T05:35:15.297559",
                "username": "test",
                "version_id": "2f07734529a83242"
            }]""",
        )
        la = LoggedAction.objects.create(
            person=person, popit_person_new_version="3fc494d54f61a157"
        )
        self.assertEqual(
            tidy_html_whitespace(la.diff_html),
            "<dl><dt>Changes made compared to parent 2f07734529a83242</dt>"
            '<dd><p class="version-diff">'
            '<span class="version-op-remove" style="color: #8e2424">'
            "Removed: email (previously it was &quot;sarah@example.com&quot;)"
            "</span><br/></p></dd></dl>",
        )
