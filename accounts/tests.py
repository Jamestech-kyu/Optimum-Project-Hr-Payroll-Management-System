from django.test import TestCase
from accounts import models as accounts_models


class UserDelegationModelTests(TestCase):
    def test_user_delegation_model_is_available(self):
        self.assertTrue(hasattr(accounts_models, "UserDelegation"))
