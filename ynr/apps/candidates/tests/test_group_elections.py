from collections import OrderedDict
import datetime

from django.test import TestCase

from elections.models import Election

from .uk_examples import UK2015ExamplesMixin
from .factories import ElectionFactory


def get_election_extra(post, election):
    return post.ballot_set.get(election=election)


class TestElectionGrouping(UK2015ExamplesMixin, TestCase):

    maxDiff = None

    def setUp(self):
        super().setUp()
        self.sp_c_election = ElectionFactory(
            slug="sp.c.2016-05-05",
            name="2016 Scottish Parliament Election (Constituencies)",
            election_date="2016-05-05",
            for_post_role="Member of the Scottish Parliament",
        )
        self.sp_r_election = ElectionFactory(
            slug="sp.r.2016-05-05",
            name="2016 Scottish Parliament Election (Regions)",
            election_date="2016-05-05",
            for_post_role="Member of the Scottish Parliament",
        )

    def test_election_grouping(self):
        with self.assertNumQueries(1):
            self.assertEqual(
                Election.group_and_order_elections(),
                [
                    {
                        "current_or_future": True,
                        "dates": OrderedDict(
                            [
                                (
                                    datetime.date(2016, 5, 5),
                                    [
                                        {
                                            "role": "Local Councillor",
                                            "elections": [
                                                {
                                                    "election": self.local_election
                                                }
                                            ],
                                        },
                                        {
                                            "role": "Member of the Scottish Parliament",
                                            "elections": [
                                                {
                                                    "election": self.sp_c_election
                                                },
                                                {
                                                    "election": self.sp_r_election
                                                },
                                            ],
                                        },
                                    ],
                                ),
                                (
                                    self.election.election_date,
                                    [
                                        {
                                            "role": "Member of Parliament",
                                            "elections": [
                                                {"election": self.election}
                                            ],
                                        }
                                    ],
                                ),
                            ]
                        ),
                    },
                    {
                        "current_or_future": False,
                        "dates": OrderedDict(
                            [
                                (
                                    self.earlier_election.election_date,
                                    [
                                        {
                                            "role": "Member of Parliament",
                                            "elections": [
                                                {
                                                    "election": self.earlier_election
                                                }
                                            ],
                                        }
                                    ],
                                )
                            ]
                        ),
                    },
                ],
            )

    def test_election_grouping_with_posts(self):
        camberwell_ballot = get_election_extra(
            self.camberwell_post, self.election
        )
        dulwich_ballot = get_election_extra(self.dulwich_post, self.election)
        edinburgh_east_ballot = get_election_extra(
            self.edinburgh_east_post, self.election
        )
        edinburgh_north_ballot = get_election_extra(
            self.edinburgh_north_post, self.election
        )
        camberwell_earlier = get_election_extra(
            self.camberwell_post, self.earlier_election
        )
        dulwich_earlier = get_election_extra(
            self.dulwich_post, self.earlier_election
        )
        edinburgh_east_earlier = get_election_extra(
            self.edinburgh_east_post, self.earlier_election
        )
        edinburgh_north_earlier = get_election_extra(
            self.edinburgh_north_post, self.earlier_election
        )
        local_council_ballot = get_election_extra(
            self.local_post, self.local_election
        )
        with self.assertNumQueries(3):
            self.assertEqual(
                Election.group_and_order_elections(include_ballots=True),
                [
                    {
                        "current_or_future": True,
                        "dates": OrderedDict(
                            [
                                (
                                    datetime.date(2016, 5, 5),
                                    [
                                        {
                                            "role": "Local Councillor",
                                            "elections": [
                                                {
                                                    "ballots": [
                                                        local_council_ballot
                                                    ],
                                                    "election": self.local_election,
                                                }
                                            ],
                                        },
                                        {
                                            "role": "Member of the Scottish Parliament",
                                            "elections": [
                                                {
                                                    "ballots": [],
                                                    "election": self.sp_c_election,
                                                },
                                                {
                                                    "ballots": [],
                                                    "election": self.sp_r_election,
                                                },
                                            ],
                                        },
                                    ],
                                ),
                                (
                                    self.election.election_date,
                                    [
                                        {
                                            "role": "Member of Parliament",
                                            "elections": [
                                                {
                                                    "ballots": [
                                                        camberwell_ballot,
                                                        dulwich_ballot,
                                                        edinburgh_east_ballot,
                                                        edinburgh_north_ballot,
                                                    ],
                                                    "election": self.election,
                                                }
                                            ],
                                        }
                                    ],
                                ),
                            ]
                        ),
                    },
                    {
                        "current_or_future": False,
                        "dates": OrderedDict(
                            [
                                (
                                    self.earlier_election.election_date,
                                    [
                                        {
                                            "role": "Member of Parliament",
                                            "elections": [
                                                {
                                                    "ballots": [
                                                        camberwell_earlier,
                                                        dulwich_earlier,
                                                        edinburgh_east_earlier,
                                                        edinburgh_north_earlier,
                                                    ],
                                                    "election": self.earlier_election,
                                                }
                                            ],
                                        }
                                    ],
                                )
                            ]
                        ),
                    },
                ],
            )

    def test_election_just_general_elections(self):
        self.sp_c_election.delete()
        self.sp_r_election.delete()
        with self.assertNumQueries(1):
            self.assertEqual(
                Election.group_and_order_elections(),
                [
                    {
                        "current_or_future": True,
                        "dates": OrderedDict(
                            [
                                (
                                    self.local_election.election_date,
                                    [
                                        {
                                            "role": "Local Councillor",
                                            "elections": [
                                                {
                                                    "election": self.local_election
                                                }
                                            ],
                                        }
                                    ],
                                ),
                                (
                                    self.election.election_date,
                                    [
                                        {
                                            "role": "Member of Parliament",
                                            "elections": [
                                                {"election": self.election}
                                            ],
                                        }
                                    ],
                                ),
                            ]
                        ),
                    },
                    {
                        "current_or_future": False,
                        "dates": OrderedDict(
                            [
                                (
                                    self.earlier_election.election_date,
                                    [
                                        {
                                            "role": "Member of Parliament",
                                            "elections": [
                                                {
                                                    "election": self.earlier_election
                                                }
                                            ],
                                        }
                                    ],
                                )
                            ]
                        ),
                    },
                ],
            )
