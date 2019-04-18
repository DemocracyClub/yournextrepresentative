from django.test import TestCase

from people.tests.factories import PersonFactory
from people.models import PersonIdentifier


class TestPersonIdentifiers(TestCase):
    def setUp(self):
        self.person = PersonFactory(pk=1)

    def test_str(self):

        pi = PersonIdentifier.objects.create(
            person=self.person,
            value="democlub",
            value_type="twitter_username",
            internal_identifier="2324",
        )
        self.assertEqual(str(pi), "1: twitter_username (democlub)")

    def test_get_value_html_twitter(self):
        pi = PersonIdentifier.objects.create(
            person=self.person,
            value="democlub",
            value_type="twitter_username",
            internal_identifier="2324",
        )

        # Test the value HTML
        self.assertEqual(
            pi.get_value_html,
            """<a href="https://twitter.com/democlub" rel="nofollow">democlub</a>""",
        )

        # Test the value type HTML
        self.assertEqual(pi.get_value_type_html, "Twitter")

    def test_get_value_html_url(self):
        pi = PersonIdentifier.objects.create(
            person=self.person,
            value="https://example.com/",
            value_type="homepage",
        )

        self.assertEqual(
            pi.get_value_html,
            """<a href="https://example.com/" rel="nofollow">https://example.com/</a>""",
        )

    def test_get_value_html_attempted_xss(self):
        pi = PersonIdentifier.objects.create(
            person=self.person,
            value="<script>alert('foo');</script>",
            value_type="homepage",
        )

        self.assertEqual(
            pi.get_value_html,
            """&lt;script&gt;alert(&#39;foo&#39;);&lt;/script&gt;""",
        )

    def test_get_value_html_bad_strings(self):
        """
        Some strings from https://github.com/minimaxir/big-list-of-naughty-strings/blob/master/blns.txt
        :return:
        """
        bad_strings = {
            "Œ„´‰ˇÁ¨ˆØ∏”’": "Œ„´‰ˇÁ¨ˆØ∏”’",
            "👾 🙇 💁 🙅 🙆 🙋 🙎 🙍": "👾 🙇 💁 🙅 🙆 🙋 🙎 🙍",
            "&lt;script&gt;alert(&#39;123&#39;);&lt;/script&gt;": "&amp;lt;script&amp;gt;alert(&amp;#39;123&amp;#39;);&amp;lt;/script&amp;gt;",
            "<IMG SRC=&#x6A&#x61&#x76&#x61&#x73&#x63&#x72&#x69&#x70&#x74&#x3A&#x61&#x6C&#x65&#x72&#x74&#x28&#x27&#x58&#x53&#x53&#x27&#x29>": "&lt;IMG SRC=&amp;#x6A&amp;#x61&amp;#x76&amp;#x61&amp;#x73&amp;#x63&amp;#x72&amp;#x69&amp;#x70&amp;#x74&amp;#x3A&amp;#x61&amp;#x6C&amp;#x65&amp;#x72&amp;#x74&amp;#x28&amp;#x27&amp;#x58&amp;#x53&amp;#x53&amp;#x27&amp;#x29&gt;",
        }

        for bad, expected in bad_strings.items():
            pi = PersonIdentifier(
                person=self.person, value=bad, value_type="homepage"
            )

            self.assertEqual(pi.get_value_html, expected)
