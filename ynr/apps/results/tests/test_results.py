from io import BytesIO

from django.utils.feedgenerator import rfc3339_date
from django_webtest import WebTest
from lxml import etree

import people.tests.factories
from candidates.tests.auth import TestUserMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin
from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME
from people.models import PersonImage
from results.models import ResultEvent


class XMLEqualityMixin(object):

    maxDiff = None

    def compare_xml(self, xml_a, xml_b):
        """Compare two XML strings under XML canonicalization

        This is insensitive to attribute order; if there is a
        different, self.assertEqual is used to generate the usual
        unequal test output, which has a helpful diff.

        This approach was suggested in:

            http://stackoverflow.com/a/12430650/223092
        """
        parser = etree.XMLParser(remove_blank_text=True)
        tree_a = etree.fromstring(xml_a, parser)
        tree_b = etree.fromstring(xml_b, parser)
        c14n_a = BytesIO()
        c14n_b = BytesIO()
        tree_a.getroottree().write_c14n(c14n_a)
        tree_b.getroottree().write_c14n(c14n_b)
        if c14n_a.getvalue() != c14n_b.getvalue():
            self.assertEqual(xml_a, xml_b)


class TestResultsFeed(
    XMLEqualityMixin, TestUserMixin, UK2015ExamplesMixin, WebTest
):
    def setUp(self):
        super().setUp()
        person = people.tests.factories.PersonFactory.create(
            id=4322, name="Tessa Jowell"
        )
        example_image_filename = EXAMPLE_IMAGE_FILENAME
        self.example_image = PersonImage.objects.create_from_file(
            filename=example_image_filename,
            new_filename="images/jowell-pilot.jpg",
            defaults={
                "person": person,
                "source": "Taken from Wikipedia",
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "A photo of Tessa Jowell",
            },
        )
        ResultEvent.objects.create(
            election=self.election,
            winner=person,
            post=self.dulwich_post,
            winner_party=self.labour_party,
            source="Seen on the BBC news",
            user=self.user,
            parlparse_id="uk.org.publicwhip/person/123456",
        )

    def test_all_feed_with_one_item(self):
        response = self.app.get("/results/all.atom")
        root = etree.XML(response.content)
        xml_pretty = etree.tounicode(root, pretty_print=True)

        result_event = ResultEvent.objects.first()
        expected = """<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-gb">
  <title>Election results from example.com (with extra data)</title>
  <link href="http://example.com/" rel="alternate"/>
  <link href="http://example.com/results/all.atom" rel="self"/>
  <id>http://example.com/</id>
  <updated>{updated}</updated>
  <entry>
    <title>Tessa Jowell (Labour Party) won in Dulwich and West Norwood</title>
    <link href="http://example.com/#{item_id}" rel="alternate"/>
    <published>{updated}</published>
    <updated>{updated}</updated>
    <author>
      <name>john</name>
    </author>
    <id>http://example.com/#{item_id}</id>
    <summary type="html">A example.com volunteer recorded at {space_separated} that Tessa Jowell (Labour Party) won the ballot in Dulwich and West Norwood, quoting the source 'Seen on the BBC news'.</summary>
    <retraction>0</retraction>
    <election_slug>parl.2015-05-07</election_slug>
    <election_name>2015 General Election</election_name>
    <election_date>{election_date}</election_date>
    <post_id>65808</post_id>
    <winner_person_id>4322</winner_person_id>
    <winner_person_name>Tessa Jowell</winner_person_name>
    <winner_party_id>party:53</winner_party_id>
    <winner_party_name>Labour Party</winner_party_name>
    <user_id>{user_id}</user_id>
    <post_name>Dulwich and West Norwood</post_name>
    <information_source>Seen on the BBC news</information_source>
    <image_url>https://example.com{image_url_path}</image_url>
    <parlparse_id>uk.org.publicwhip/person/123456</parlparse_id>
  </entry>
</feed>
""".format(
            updated=rfc3339_date(result_event.created),
            space_separated=result_event.created.strftime("%Y-%m-%d %H:%M:%S"),
            item_id=result_event.id,
            user_id=self.user.id,
            election_date=self.election.election_date,
            image_url_path=self.example_image.image.url,
        )
        self.compare_xml(expected, xml_pretty)

    def test_all_basic_feed_with_one_item(self):
        response = self.app.get("/results/all-basic.atom")
        root = etree.XML(response.content)
        xml_pretty = etree.tounicode(root, pretty_print=True)

        result_event = ResultEvent.objects.first()
        expected = """<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-gb">
  <title>Election results from example.com</title>
  <link href="http://example.com/" rel="alternate"/>
  <link href="http://example.com/results/all-basic.atom" rel="self"/>
  <id>http://example.com/</id>
  <updated>{updated}</updated>
  <entry>
    <title>Tessa Jowell (Labour Party) won in Dulwich and West Norwood</title>
    <link href="http://example.com/#{item_id}" rel="alternate"/>
    <published>{updated}</published>
    <updated>{updated}</updated>
    <author>
      <name>john</name>
    </author>
    <id>http://example.com/#{item_id}</id>
    <summary type="html">A example.com volunteer recorded at {space_separated} that Tessa Jowell (Labour Party) won the ballot in Dulwich and West Norwood, quoting the source 'Seen on the BBC news'.</summary>
  </entry>
</feed>
""".format(
            updated=rfc3339_date(result_event.created),
            space_separated=result_event.created.strftime("%Y-%m-%d %H:%M:%S"),
            item_id=result_event.id,
        )
        self.compare_xml(expected, xml_pretty)


class TestResultsFeedWithRetraction(
    XMLEqualityMixin, TestUserMixin, UK2015ExamplesMixin, WebTest
):
    def setUp(self):
        super().setUp()
        accidental_winner = people.tests.factories.PersonFactory.create(
            id="4322", name="Tessa Jowell"
        )
        real_winner = people.tests.factories.PersonFactory.create(
            id="4493", name="James Barber"
        )
        ResultEvent.objects.create(
            election=self.election,
            winner=accidental_winner,
            post=self.dulwich_post,
            winner_party=self.labour_party,
            source="Seen on the BBC news",
            user=self.user,
            parlparse_id="uk.org.publicwhip/person/123456",
        )
        ResultEvent.objects.create(
            election=self.election,
            winner=accidental_winner,
            post=self.dulwich_post,
            winner_party=self.labour_party,
            source="Result recorded in error, retracting",
            user=self.user,
            parlparse_id="uk.org.publicwhip/person/123456",
            retraction=True,
        )
        ResultEvent.objects.create(
            election=self.election,
            winner=real_winner,
            post=self.dulwich_post,
            winner_party=self.ld_party,
            source="Seen on Sky News",
            user=self.user,
        )
        # This is ordered by default:
        self.events = ResultEvent.objects.all()

    def test_all_feed_with_a_correction(self):
        response = self.app.get("/results/all.atom")
        root = etree.XML(response.content)
        xml_pretty = etree.tounicode(root, pretty_print=True)

        expected = """<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-gb">
  <title>Election results from example.com (with extra data)</title>
  <link href="http://example.com/" rel="alternate"/>
  <link href="http://example.com/results/all.atom" rel="self"/>
  <id>http://example.com/</id>
  <updated>{updated[2]}</updated>
  <entry>
    <title>Tessa Jowell (Labour Party) won in Dulwich and West Norwood</title>
    <link href="http://example.com/#{item_id[0]}" rel="alternate"/>
    <published>{updated[0]}</published>
    <updated>{updated[0]}</updated>
    <author>
      <name>john</name>
    </author>
    <id>http://example.com/#{item_id[0]}</id>
    <summary type="html">A example.com volunteer recorded at {space_separated[0]} that Tessa Jowell (Labour Party) won the ballot in Dulwich and West Norwood, quoting the source 'Seen on the BBC news'.</summary>
    <retraction>0</retraction>
    <election_slug>parl.2015-05-07</election_slug>
    <election_name>2015 General Election</election_name>
    <election_date>{election_date}</election_date>
    <post_id>65808</post_id>
    <winner_person_id>4322</winner_person_id>
    <winner_person_name>Tessa Jowell</winner_person_name>
    <winner_party_id>party:53</winner_party_id>
    <winner_party_name>Labour Party</winner_party_name>
    <user_id>{user_id}</user_id>
    <post_name>Dulwich and West Norwood</post_name>
    <information_source>Seen on the BBC news</information_source>
    <parlparse_id>uk.org.publicwhip/person/123456</parlparse_id>
  </entry>
  <entry>
    <title>Correction: retracting the statement that Tessa Jowell (Labour Party) won in Dulwich and West Norwood</title>
    <link href="http://example.com/#{item_id[1]}" rel="alternate"/>
    <published>{updated[1]}</published>
    <updated>{updated[1]}</updated>
    <author>
      <name>john</name>
    </author>
    <id>http://example.com/#{item_id[1]}</id>
    <summary type="html">At {space_separated[1]}, a example.com volunteer retracted the previous assertion that Tessa Jowell (Labour Party) won the ballot in Dulwich and West Norwood, quoting the source 'Result recorded in error, retracting'.</summary>
    <retraction>1</retraction>
    <election_slug>parl.2015-05-07</election_slug>
    <election_name>2015 General Election</election_name>
    <election_date>{election_date}</election_date>
    <post_id>65808</post_id>
    <winner_person_id>4322</winner_person_id>
    <winner_person_name>Tessa Jowell</winner_person_name>
    <winner_party_id>party:53</winner_party_id>
    <winner_party_name>Labour Party</winner_party_name>
    <user_id>{user_id}</user_id>
    <post_name>Dulwich and West Norwood</post_name>
    <information_source>Result recorded in error, retracting</information_source>
    <parlparse_id>uk.org.publicwhip/person/123456</parlparse_id>
  </entry>
  <entry>
    <title>James Barber (Liberal Democrats) won in Dulwich and West Norwood</title>
    <link href="http://example.com/#{item_id[2]}" rel="alternate"/>
    <published>{updated[2]}</published>
    <updated>{updated[2]}</updated>
    <author>
      <name>john</name>
    </author>
    <id>http://example.com/#{item_id[2]}</id>
    <summary type="html">A example.com volunteer recorded at {space_separated[2]} that James Barber (Liberal Democrats) won the ballot in Dulwich and West Norwood, quoting the source 'Seen on Sky News'.</summary>
    <retraction>0</retraction>
    <election_slug>parl.2015-05-07</election_slug>
    <election_name>2015 General Election</election_name>
    <election_date>{election_date}</election_date>
    <post_id>65808</post_id>
    <winner_person_id>4493</winner_person_id>
    <winner_person_name>James Barber</winner_person_name>
    <winner_party_id>party:90</winner_party_id>
    <winner_party_name>Liberal Democrats</winner_party_name>
    <user_id>{user_id}</user_id>
    <post_name>Dulwich and West Norwood</post_name>
    <information_source>Seen on Sky News</information_source>
  </entry>
</feed>
""".format(
            updated=[
                rfc3339_date(result_event.created)
                for result_event in self.events
            ],
            space_separated=[
                result_event.created.strftime("%Y-%m-%d %H:%M:%S")
                for result_event in self.events
            ],
            item_id=[result_event.id for result_event in self.events],
            user_id=self.user.id,
            election_date=self.election.election_date,
        )
        self.compare_xml(expected, xml_pretty)

    def test_all_basic_feed_with_a_correction(self):
        response = self.app.get("/results/all-basic.atom")
        root = etree.XML(response.content)
        xml_pretty = etree.tounicode(root, pretty_print=True)

        expected = """<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="en-gb">
  <title>Election results from example.com</title>
  <link href="http://example.com/" rel="alternate"/>
  <link href="http://example.com/results/all-basic.atom" rel="self"/>
  <id>http://example.com/</id>
  <updated>{updated[2]}</updated>
  <entry>
    <title>Tessa Jowell (Labour Party) won in Dulwich and West Norwood</title>
    <link href="http://example.com/#{item_id[0]}" rel="alternate"/>
    <published>{updated[0]}</published>
    <updated>{updated[0]}</updated>
    <author>
      <name>john</name>
    </author>
    <id>http://example.com/#{item_id[0]}</id>
    <summary type="html">A example.com volunteer recorded at {space_separated[0]} that Tessa Jowell (Labour Party) won the ballot in Dulwich and West Norwood, quoting the source 'Seen on the BBC news'.</summary>
  </entry>
  <entry>
    <title>Correction: retracting the statement that Tessa Jowell (Labour Party) won in Dulwich and West Norwood</title>
    <link href="http://example.com/#{item_id[1]}" rel="alternate"/>
    <published>{updated[1]}</published>
    <updated>{updated[1]}</updated>
    <author>
      <name>john</name>
    </author>
    <id>http://example.com/#{item_id[1]}</id>
    <summary type="html">At {space_separated[1]}, a example.com volunteer retracted the previous assertion that Tessa Jowell (Labour Party) won the ballot in Dulwich and West Norwood, quoting the source 'Result recorded in error, retracting'.</summary>
  </entry>
  <entry>
    <title>James Barber (Liberal Democrats) won in Dulwich and West Norwood</title>
    <link href="http://example.com/#{item_id[2]}" rel="alternate"/>
    <published>{updated[2]}</published>
    <updated>{updated[2]}</updated>
    <author>
      <name>john</name>
    </author>
    <id>http://example.com/#{item_id[2]}</id>
    <summary type="html">A example.com volunteer recorded at {space_separated[2]} that James Barber (Liberal Democrats) won the ballot in Dulwich and West Norwood, quoting the source 'Seen on Sky News'.</summary>
  </entry>
</feed>
""".format(
            updated=[
                rfc3339_date(result_event.created)
                for result_event in self.events
            ],
            space_separated=[
                result_event.created.strftime("%Y-%m-%d %H:%M:%S")
                for result_event in self.events
            ],
            item_id=[result_event.id for result_event in self.events],
        )
        self.compare_xml(expected, xml_pretty)
