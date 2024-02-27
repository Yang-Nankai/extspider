# -*- coding: utf-8 -*-
import re
from unittest import TestCase
from pathlib import Path
from extspider.common.utils import (is_valid_extension_id,
                                    get_random_extension_id)
from extspider.common.context import TEST_SAMPLES_PATH

SAMPLES_ROOT = Path(TEST_SAMPLES_PATH) / "chrome_extension_details"


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

    def test_get_random_extension_id(self):
        random_id = get_random_extension_id()
        result = re.match(r'[a-p]{32}', random_id)
        self.assertIsNotNone(result)