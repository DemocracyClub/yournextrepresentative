from django.utils import timezone

from elections.models import Election
from elections import helpers


class TestHelpers:
    def test_four_weeks_before_election_date(self):
        election = Election(election_date=timezone.datetime(2021, 5, 6).date())
        expected = timezone.datetime(2021, 4, 8, 0, 0, 0, tzinfo=timezone.utc)
        result = helpers.four_weeks_before_election_date(election=election)
        assert result == expected
