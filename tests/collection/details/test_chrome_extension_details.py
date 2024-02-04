# -*- coding: utf-8 -*-
import json
import os
from unittest import TestCase

import requests
from extspider.common.exception import ExtensionRequestError
from extspider.collection.details.chrome_extension_details import ChromeExtensionDetails
from extspider.collection.parsers.chrome_parser import ChromeExtensionResponseMapper

from extspider.common.context import TEST_SAMPLES_PATH

SAMPLES_ROOT = os.path.join(TEST_SAMPLES_PATH, "chrome_extension_details")
TEST_DOWNLOAD_PATH = os.path.join(SAMPLES_ROOT, "test_download.crx")

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        "AppleWebKit/537.36 (KHTML, like Gecko)"
        "Chrome/118.0.5993.90"
    ),
    "Host": "chromewebstore.google.com",
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
}


class TestChromeExtensionDetails(TestCase):

    def test_get_extension_detail(self):
        extension = ChromeExtensionDetails("knkpjhkhlfebmefnommmehegjgglnkdm")
        processed_data = extension.get_extension_detail()
        self.assertIsInstance(processed_data, list)
        self.assertIsNotNone(processed_data)
        self.assertGreater(len(processed_data), 0)

    def test_update_details(self):
        extension = ChromeExtensionDetails("knkpjhkhlfebmefnommmehegjgglnkdm")
        has_changed = extension.update_details()
        self.assertTrue(has_changed)
        has_changed = extension.update_details()
        self.assertFalse(has_changed)

    def test_download(self):
        extension = ChromeExtensionDetails("knkpjhkhlfebmefnommmehegjgglnkdm")
        extension.download(TEST_DOWNLOAD_PATH)
        file_exists = os.path.exists(TEST_DOWNLOAD_PATH)
        self.assertTrue(file_exists)
