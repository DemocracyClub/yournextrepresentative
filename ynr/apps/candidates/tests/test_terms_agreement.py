from django.contrib.auth.models import User
from django.test import TestCase


class Test(TestCase):
    def test_user_creation_creates_terms_agreement(self):
        u = User.objects.create_user(
            "john", "john@example.com", "notagoodpassword"
        )
        self.assertFalse(u.terms_agreement.assigned_to_dc)
