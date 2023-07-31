from elections.filters import BallotFilter
from mock import MagicMock


class TestBallotFilter:
    def test_filter_last_updated(self):
        """
        Test that the BallotFilter calls the queryset method rather
        than the method defined on the LastUpdatedMixin
        """
        queryset = MagicMock()
        filter_obj = BallotFilter(queryset=queryset)
        fieldname = "modified"
        timestamp = "timestamp"
        filter_obj.filter_last_updated(
            queryset=queryset, name=fieldname, value=timestamp
        )
        queryset.last_updated.assert_called_once_with(datetime="timestamp")
