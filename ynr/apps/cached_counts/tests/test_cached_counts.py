import json

from django_webtest import WebTest

import people.tests.factories
from people.models import Person

from candidates.tests import factories
from candidates.tests.uk_examples import UK2015ExamplesMixin

from compat import text_type


class CachedCountTestCase(UK2015ExamplesMixin, WebTest):
    maxDiff = None

    def setUp(self):
        super().setUp()
        posts = [
            self.edinburgh_east_post,
            self.edinburgh_north_post,
            self.dulwich_post,
            self.camberwell_post,
        ]
        parties = [
            self.labour_party,
            self.ld_party,
            self.green_party,
            self.conservative_party,
            self.sinn_fein,
        ]
        i = 0
        candidacy_counts = {"14419": 10, "14420": 3, "65808": 5, "65913": 0}
        for post in posts:
            candidacy_count = candidacy_counts[post.slug]
            for n in range(candidacy_count):
                person = people.tests.factories.PersonFactory.create(
                    id=str(7000 + i), name="Test Candidate {}".format(i)
                )
                party = parties[n % 5]
                factories.MembershipFactory.create(
                    person=person,
                    post=post,
                    party=party,
                    ballot=self.election.ballot_set.get(post=post),
                )
                i += 1
        # Now create a couple of candidacies in the earlier election.
        # First, one sticking with the same party (but in a different
        # post):
        factories.MembershipFactory.create(
            person=Person.objects.get(id=7000),
            post=posts[1],
            party=parties[0],
            ballot=self.earlier_election.ballot_set.get(post=posts[1]),
        )
        # Now one in the same post but standing for a different party:
        factories.MembershipFactory.create(
            person=Person.objects.get(id=7001),
            post=posts[1],
            party=parties[2],
            ballot=self.earlier_election.ballot_set.get(post=posts[1]),
        )

    def test_reports_top_page(self):
        response = self.app.get("/numbers/")
        self.assertEqual(response.status_code, 200)
        current_div = response.html.find(
            "div", {"id": "statistics-election-parl-2015-05-07"}
        )
        self.assertTrue(current_div)
        self.assertIn("Total candidates: 18", str(current_div))
        earlier_div = response.html.find(
            "div", {"id": "statistics-election-parl-2010-05-06"}
        )
        self.assertIn("Total candidates: 2", str(earlier_div))

    def test_reports_top_page_json(self):
        response = self.app.get("/numbers/?format=json")
        data = json.loads(response.body.decode("utf-8"))
        self.assertEqual(
            data,
            [
                {
                    "current_or_future": True,
                    "dates": {
                        text_type(self.election.election_date.isoformat()): [
                            {
                                "elections": [
                                    {
                                        "html_id": "parl-2015-05-07",
                                        "id": "parl.2015-05-07",
                                        "name": "2015 General Election",
                                        "total": 18,
                                    }
                                ],
                                "role": "Member of Parliament",
                            }
                        ],
                        text_type(
                            self.local_election.election_date.isoformat()
                        ): [
                            {
                                "elections": [
                                    {
                                        "html_id": "local-maidstone-2016-05-05",
                                        "id": "local.maidstone.2016-05-05",
                                        "name": "Maidstone local election",
                                        "total": 0,
                                    }
                                ],
                                "role": "Local Councillor",
                            }
                        ],
                    },
                },
                {
                    "current_or_future": False,
                    "dates": {
                        text_type(
                            self.earlier_election.election_date.isoformat()
                        ): [
                            {
                                "elections": [
                                    {
                                        "html_id": "parl-2010-05-06",
                                        "id": "parl.2010-05-06",
                                        "name": "2010 General Election",
                                        "total": 2,
                                    }
                                ],
                                "role": "Member of Parliament",
                            }
                        ]
                    },
                },
            ],
        )

    def test_attention_needed_page(self):
        response = self.app.get("/numbers/attention-needed")
        rows = [
            tuple(td.decode() for td in row.find_all("td"))
            for row in response.html.find_all("tr")
        ]

        self.assertEqual(
            rows,
            [
                (
                    "<td>2015 General Election</td>",
                    '<td><a href="/elections/parl.65913.2015-05-07/">Camberwell and Peckham</a></td>',
                    "<td>0</td>",
                ),
                (
                    "<td>Maidstone local election</td>",
                    '<td><a href="/elections/local.maidstone.DIW:E05005004.2016-05-05/">Shepway South Ward</a></td>',
                    "<td>0</td>",
                ),
                (
                    "<td>2015 General Election</td>",
                    '<td><a href="/elections/parl.14420.2015-05-07/">Edinburgh North and Leith</a></td>',
                    "<td>3</td>",
                ),
                (
                    "<td>2015 General Election</td>",
                    '<td><a href="/elections/parl.65808.2015-05-07/">Dulwich and West Norwood</a></td>',
                    "<td>5</td>",
                ),
                (
                    "<td>2015 General Election</td>",
                    '<td><a href="/elections/parl.14419.2015-05-07/">Edinburgh East</a></td>',
                    "<td>10</td>",
                ),
            ],
        )

    def test_post_counts_page(self):
        response = self.app.get("/numbers/election/parl.2015-05-07/posts")
        self.assertEqual(response.status_code, 200)
        rows = [
            tuple(td.decode() for td in row.find_all("td"))
            for row in response.html.find_all("tr")
        ]
        self.assertEqual(
            rows,
            [
                (
                    '<td><a href="/elections/parl.14419.2015-05-07/">Member of Parliament for Edinburgh East</a></td>',
                    "<td>10</td>",
                ),
                (
                    '<td><a href="/elections/parl.65808.2015-05-07/">Member of Parliament for Dulwich and West Norwood</a></td>',
                    "<td>5</td>",
                ),
                (
                    '<td><a href="/elections/parl.14420.2015-05-07/">Member of Parliament for Edinburgh North and Leith</a></td>',
                    "<td>3</td>",
                ),
                (
                    '<td><a href="/elections/parl.65913.2015-05-07/">Member of Parliament for Camberwell and Peckham</a></td>',
                    "<td>0</td>",
                ),
            ],
        )

    def test_party_counts_page(self):
        response = self.app.get("/numbers/election/parl.2015-05-07/parties")
        self.assertEqual(response.status_code, 200)
        rows = [
            tuple(td.decode() for td in row.find_all("td"))
            for row in response.html.find_all("tr")
        ]
        self.assertEqual(
            rows,
            [
                (
                    '<td><a href="/parties/PP63/elections/parl.2015-05-07/">Green Party</a></td>',
                    "<td>4</td>",
                ),
                (
                    '<td><a href="/parties/PP53/elections/parl.2015-05-07/">Labour Party</a></td>',
                    "<td>4</td>",
                ),
                (
                    '<td><a href="/parties/PP90/elections/parl.2015-05-07/">Liberal Democrats</a></td>',
                    "<td>4</td>",
                ),
                (
                    '<td><a href="/parties/PP52/elections/parl.2015-05-07/">Conservative Party</a></td>',
                    "<td>3</td>",
                ),
                (
                    '<td><a href="/parties/PP39/elections/parl.2015-05-07/">Sinn F\xe9in</a></td>',
                    "<td>3</td>",
                ),
            ],
        )
