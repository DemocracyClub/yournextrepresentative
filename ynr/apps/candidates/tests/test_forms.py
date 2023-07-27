from unittest.mock import MagicMock

import pytest
from candidates.forms import ToggleLockForm
from candidates.models import Ballot
from django.core.exceptions import ValidationError


class TestToggleLockForm:
    @pytest.fixture
    def form_obj(self):
        ballot = MagicMock(spec=Ballot, hashed_memberships="updatedhash")
        form = ToggleLockForm()
        form.instance = ballot
        return form

    def test_clean_lock_validation_error(self, form_obj):
        form_obj.cleaned_data = {
            "lock": "lock",
            "hashed_memberships": "oldhash",
        }

        with pytest.raises(ValidationError) as e:
            form_obj.clean()
            assert e.message == "Ballot has changed, please recheck"

    def test_clean_candidates_locked(self, form_obj):
        form_obj.cleaned_data = {
            "lock": "lock",
            "hashed_memberships": "updatedhash",
        }

        result = form_obj.clean()
        assert result["candidates_locked"] is True

    def test_clean_candidates_not_locked(self, form_obj):
        form_obj.instance.candidates_locked = True
        form_obj.data = {}
        form_obj.cleaned_data = {}

        result = form_obj.clean()
        assert result["candidates_locked"] is False
