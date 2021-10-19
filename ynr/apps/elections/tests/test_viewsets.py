import mock

from django.utils import timezone
from rest_framework.test import APIRequestFactory

from elections.api.next.api_views import BallotViewSet


class TestBallotViewSet:
    def test_get_queryset_last_updated_ordered_by_modified(self):
        factory = APIRequestFactory()
        timestamp = timezone.now().isoformat()
        request = factory.get("/next/ballots/", {"last_updated": timestamp})
        request.query_params = request.GET

        view = BallotViewSet(request=request)
        view.queryset = mock.MagicMock()

        view.get_queryset()
        view.queryset.order_by.assert_called_once_with("modified")

    def test_get_queryset_last_updated_not_ordered(self):
        factory = APIRequestFactory()
        request = factory.get("/next/ballots/")
        request.query_params = request.GET

        view = BallotViewSet(request=request)
        view.queryset = mock.MagicMock()

        view.get_queryset()
        view.queryset.order_by.assert_not_called()

    def test_get_queryset_max_items(self):
        factory = APIRequestFactory()
        request = factory.get("/next/ballots/", {"max_items": 200})
        request.query_params = request.GET
        view = BallotViewSet(request=request)

        # represents qs of 1000 ballots
        ballots = list(range(1000))
        view.queryset = ballots

        queryset = view.get_queryset()
        assert len(queryset) == 200

    def test_get_queryset_max_items_not_used(self):
        factory = APIRequestFactory()
        request = factory.get("/next/ballots/")
        request.query_params = request.GET
        view = BallotViewSet(request=request)

        # represents qs of 1000 ballots
        ballots = list(range(1000))
        view.queryset = ballots

        queryset = view.get_queryset()
        assert len(queryset) == 1000
