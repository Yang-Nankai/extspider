# -*- coding: utf-8 -*-
import json
import os
from unittest import TestCase
from dataclasses import fields
from datetime import date, datetime
from extspider.common.context import TEST_SAMPLES_PATH
from extspider.collection.parsers.chrome_parser import ChromeExtensionDetailsMapper, ChromeCategoryResponseMapper
from extspider.collection.details.chrome_extension_details import ChromeExtensionDetails
from extspider.common.exception import UnexpectedDataStructure

# region TEST SAMPLES INITIALISATION
SAMPLES_ROOT = os.path.join(TEST_SAMPLES_PATH, "chrome_parser")


def read_sample(file_name):
    file_path = os.path.join(SAMPLES_ROOT, file_name)
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def read_json_sample(file_name):
    content_string = read_sample(file_name)
    return json.loads(content_string)


# JSON raw data samples
CATEGORY_DATA = read_json_sample("lifestyle-art-data.json")
DETAILS_DATA = read_json_sample("google-translate-data.json")
BAD_DETAILS_DATA = read_json_sample("bad-extension-data.json")
DATA_SAMPLES = [CATEGORY_DATA, DETAILS_DATA]

# JSON parsed data samples
CATEGORY_PARSED = read_json_sample("lifestyle-art-parsed.json")
DETAILS_PARSED = read_json_sample("google-translate-parsed.json")
PARSED_SAMPLES = [CATEGORY_PARSED, DETAILS_PARSED]


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)

class TestChromeCategoryResponseMapper(TestCase):
    def test_map_data_list(self):
        parsed_data = ChromeCategoryResponseMapper.map_data_list(CATEGORY_DATA)
        self.assertEqual(parsed_data, CATEGORY_PARSED)


class TestChromeExtensionDetailsMapper(TestCase):

    def test_index_map(self):
        """
        Ensure that INDEX_PATH accurately represents the data attributes of
        ChromeExtensionDetails.
        """
        map_dict = ChromeExtensionDetailsMapper.INDEX_MAP
        map_keys = list(map_dict.keys())
        self.assertEqual(len(map_keys), len(fields(ChromeExtensionDetails)))
        for attribute in map_keys:
            index = ChromeExtensionDetails.get_attribute_index(attribute)
            self.assertGreater(index, -1)

    def test_map_data_list(self):
        parsed_data = ChromeExtensionDetailsMapper.map_data_list(DETAILS_DATA)
        parsed_json = json.loads(json.dumps(parsed_data, cls=ComplexEncoder))
        self.assertEqual(parsed_json, DETAILS_PARSED)

    def test_invaild_data_list(self):
        with self.assertRaises(UnexpectedDataStructure):
            parsed_data = ChromeExtensionDetailsMapper.map_data_list(BAD_DETAILS_DATA)

