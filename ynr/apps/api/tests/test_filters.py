import mock
from api.next.filters import LastUpdatedMixin
from django_webtest import WebTest
from mock import MagicMock


class TestLastUpdatedMixin(WebTest):
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

    @mock.patch("elections.uk.geo_helpers.requests")
    def test_bad_postcode_exception(self, mock_requests):
        mock_requests.get.return_value = mock.Mock(
            **{
                "json.return_value": {"detail": "Invalid postcode"},
                "status_code": 400,
            }
        )

        resp = self.client.get("/api/next/ballots/?for_postcode=SW1A 1AA")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(
            resp.json(), ['The postcode "SW1A 1AA" couldn\'t be found']
        )
