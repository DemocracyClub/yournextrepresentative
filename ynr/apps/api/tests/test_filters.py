from mock import MagicMock

from api.next.filters import LastUpdatedMixin, UncontestedMixin


class TestLastUpdatedMixin:
    def test_filter_last_updated(self):
        """
        Test that the querset is filtered using the correct fieldname
        and expression
        """
        queryset = MagicMock()
        filter_obj = LastUpdatedMixin(queryset=queryset)
        fieldname = "modified"
        timestamp = "timestamp"
        filter_obj.filter_last_updated(
            queryset=queryset, name=fieldname, value=timestamp
        )
        queryset.filter.assert_called_once_with(modified__gt=timestamp)


class TestUncontestedMixin:
    def test_filter_uncontested(self):
        """
        Test that the queryset is filtered using the correct fieldname
        and expression
        """
        queryset = MagicMock()
        filter_obj = UncontestedMixin(queryset=queryset)
        fieldname = "uncontested"
        filter_obj.filter_uncontested(queryset=queryset, name=fieldname)
