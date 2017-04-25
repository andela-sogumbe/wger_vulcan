# coding=utf-
from django.contrib.auth.models import User
from wger.core.tests.base_testcase import WorkoutManagerTestCase
from wger.core.tests.api_base_test import ApiPostTestCase


class CreateUserApiTestCase(WorkoutManagerTestCase, ApiPostTestCase):
    """
    test creating a user from a external request
    """
    object_class = User
    url = 'core:user:add'
    data = {'full_name': 'Something here',
            'short_name': 'SH'}


class CreateUserApiOverview(WorkoutManagerTestCase):
    """
    test view lists of created user
    """
    url = 'core:user:list'
