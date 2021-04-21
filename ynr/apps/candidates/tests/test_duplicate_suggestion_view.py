import pytest

from candidates.views.people import DuplicatePersonView
from people.models import Person
from people.tests.factories import PersonFactory


class TestDuplicatePersonViewUnitTests:
    @pytest.fixture
    def view_obj(self, rf):
        request = rf.get("/")
        request.GET = {}
        view = DuplicatePersonView()
        view.setup(request=request)
        view.object = Person(pk=1)
        return view

    def test_get_context_data_missing_other_param(self, view_obj):
        context = view_obj.get_context_data()
        assert "error" in context
        assert context["error"] == "Other person ID is missing"

    def test_get_context_data_missing_other_value(self, view_obj):
        view_obj.request.GET.update({"other": None})
        context = view_obj.get_context_data()
        assert "error" in context
        assert context["error"] == "Other person ID is missing"

    def test_get_context_data_other_not_number(self, view_obj):
        view_obj.request.GET.update({"other": "foo"})
        context = view_obj.get_context_data()
        assert "error" in context
        assert context["error"] == "Malformed person ID foo"

    def test_get_context_data_other_id_same_as_person(self, view_obj):
        view_obj.request.GET.update({"other": "1"})
        context = view_obj.get_context_data()
        assert "error" in context
        assert (
            context["error"] == "You can't merge a person (1) with themself (1)"
        )

    @pytest.mark.django_db
    def test_get_context_data_other_person_not_found(self, view_obj):
        view_obj.request.GET.update({"other": "2"})
        context = view_obj.get_context_data()
        assert "error" in context
        assert context["error"] == "Person not found with ID 2"

    @pytest.mark.django_db
    def test_get_context_data_other_person_added_to_context(self, view_obj):
        person = PersonFactory(pk=1234)
        view_obj.request.GET.update({"other": "1234"})
        context = view_obj.get_context_data()
        assert "error" not in context
        assert context["other_person"] == person
