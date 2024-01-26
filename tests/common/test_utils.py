# -*- coding: utf-8 -*-

from extspider.common.utils import is_valid_extension_id
from unittest import TestCase


class TestUtils(TestCase):
    """
    TestUtils ensures correct functionality of utils
    """

    def test_is_valid_extension_id(self):
        """
        test_is_valid_extension_id ensures functionality of checking extension_id
        """
        extension_id = "abcdef1234567890abcdef1234567890"
        result = is_valid_extension_id(extension_id)
        self.assertIsNot(result, True)

        extension_id = "dhdgffkkebhmkfjojejmpbldmpobfkfoa"
        result = is_valid_extension_id(extension_id)
        self.assertIsNot(result, True)

        extension_id = "Dhdgffkkebhmkfjojejmpbldmpobfkfo"
        result = is_valid_extension_id(extension_id)
        self.assertIsNot(result, True)

        extension_id = "dhdgffkkebhmkfjojejmpbldmpobfkfo"
        result = is_valid_extension_id(extension_id)
        self.assertIs(result, True)



