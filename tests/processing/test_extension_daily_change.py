# -*- coding: utf-8 -*-
# TODO: 完成extension的改变，根据id+version
#  得到的数据增加的放一起、减少的放一起、版本改变的放一起
import re
import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest import TestCase
from typing import Iterable, Optional, List, Set
from extspider.processing.extension_daily_change import (get_id_difference_set,
                                                         get_version_change_id_set,
                                                         extract_data_by_id_set)

from extspider.common.context import TEST_SAMPLES_PATH, DATA_PATH
SAMPLES_ROOT = os.path.join(TEST_SAMPLES_PATH, "processing")


class TestExtensionDailyChange(TestCase):

    def setUp(self) -> None:
        self.pre_result_path = os.path.join(SAMPLES_ROOT, "test_previous_result.csv")
        self.now_result_path = os.path.join(SAMPLES_ROOT, "test_now_result.csv")

    def test_id_add(self):
        add_set = get_id_difference_set(str(self.now_result_path),
                                        str(self.pre_result_path))
        self.assertGreater(len(add_set), 0)
        result_data = extract_data_by_id_set(str(self.now_result_path), add_set)
        self.assertGreater(len(result_data), 0)

    def test_id_del(self):
        del_set = get_id_difference_set(str(self.pre_result_path),
                                        str(self.now_result_path))
        self.assertGreater(len(del_set), 0)
        result_data = extract_data_by_id_set(str(self.pre_result_path), del_set)
        print(result_data)
        self.assertGreater(len(result_data), 0)

    def test_version_change(self):
        add_set = get_id_difference_set(str(self.now_result_path),
                                        str(self.pre_result_path))
        self.assertGreater(len(add_set), 0)
        change_set = get_version_change_id_set(add_set,
                                               str(self.now_result_path),
                                               str(self.pre_result_path))
        self.assertGreater(len(change_set), 0)
        result_data = extract_data_by_id_set(str(self.now_result_path), change_set)
        print(result_data)
        self.assertGreater(len(result_data), 0)






