# -*- coding: utf-8 -*-
import os
from unittest import TestCase
from extspider.common.context import DATA_PATH
from extspider.processing.compare_extension_ids import generate_diff_result, write_diff_result


class TestCompareExtensionIds(TestCase):

    def test_generate_diff_result(self):
        old_ids_filename = f"{DATA_PATH}/24_1_31_extension_ids.txt"
        new_ids_filename = f"{DATA_PATH}/24_2_1_extension_ids.txt"
        diff_result = generate_diff_result(old_ids_filename, new_ids_filename)

        self.assertIsInstance(diff_result, list)
        self.assertGreater(len(diff_result), 0)

        result_filename = f"{DATA_PATH}/diff_result.txt"
        write_diff_result(result_filename, diff_result)
        is_exist = os.path.exists(result_filename)
        self.assertEqual(is_exist, True)

    def tearDown(self) -> None:
        pass
