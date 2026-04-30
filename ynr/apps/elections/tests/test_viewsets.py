import mock
from django.utils import timezone
from elections.api.next.api_views import BallotViewSet
from rest_framework.test import APIRequestFactory


class TestBallotViewSet:
    def test_get_queryset_last_updated_ordered_by_modified(self):
        factory = APIRequestFactory()
        timestamp = timezone.now().isoformat()
        request = factory.get("/next/ballots/", {"last_updated": timestamp})
        request.query_params = request.GET

        view = BallotViewSet(request=request)
        view.queryset = mock.MagicMock()

        view.get_queryset()
        view.queryset.with_last_updated.assert_called_once()
        view.queryset.with_last_updated.return_value.order_by.assert_called_once_with(
            "last_updated"
        )

    def test_get_queryset_last_updated_not_ordered(self):
        factory = APIRequestFactory()
        request = factory.get("/next/ballots/")
        request.query_params = request.GET

        view = BallotViewSet(request=request)
        view.queryset = mock.MagicMock()

        view.get_queryset()
        view.queryset.with_last_updated.assert_called_once()
        view.queryset.with_last_updated.return_value.order_by.assert_not_called()
