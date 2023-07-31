from datetime import date

from django.test import TestCase
from mock import patch
from people.models import Person


@patch("people.models.date")
class TestAgeCalculation(TestCase):
    def test_age_year_ambiguous(self, mock_date):
        mock_date.today.return_value = date(1977, 9, 10)
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
        p = Person.objects.create(name="Test Person", birth_date="1975")
        self.assertEqual(p.age, "1 or 2")
