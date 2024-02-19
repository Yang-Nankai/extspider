# -*- coding: utf-8 -*-
import os
from dataclasses import astuple

from .base_tests import BaseTests as BT
from extspider.collection.details.chrome_extension_details import ChromeExtensionDetails
from extspider.common.context import TEST_SAMPLES_PATH
from extspider.common.configuration import HTTP_HEADERS

SAMPLES_ROOT = os.path.join(TEST_SAMPLES_PATH, "chrome_extension_details")
TEST_DOWNLOAD_PATH = os.path.join(SAMPLES_ROOT, "test_download.crx")
TEST_MANIFEST_PATH = os.path.join(SAMPLES_ROOT, "manifest.json")


class TestChromeExtensionDetails(BT.DetailsTestCase):

    @property
    def details_class(self):
        return ChromeExtensionDetails

    def setUp(self) -> None:
        self.extension = ChromeExtensionDetails("pgbdljpkijehgoacbjpolaomhkoffhnl")

    def test_get_extension_detail(self):
        processed_data = self.extension.get_extension_detail()
        self.assertIsNotNone(processed_data)
        self.assertEqual(len(processed_data), 13)

    def test_update_details(self):
        has_changed = self.extension.update_details()
        self.assertTrue(has_changed)
        has_changed = self.extension.update_details()
        self.assertFalse(has_changed)

    def test_download(self):
        self.extension.download(TEST_DOWNLOAD_PATH)
        crx_file_exists = os.path.exists(TEST_DOWNLOAD_PATH)
        self.assertTrue(crx_file_exists)
        manifest_file_exists = os.path.exists(TEST_MANIFEST_PATH)
        self.assertTrue(manifest_file_exists)

    def test_update_from(self):
        identifier = "a" * 32

        original = self.details_class(identifier, "test", version="1.0.0")
        change = astuple(self.details_class(identifier, "test", version="1.0.1"))
        original.update_from(change)
        self.assertEqual(original.version, "1.0.1")

    def test_copy_from(self):
        identifier = "a" * 32

        original = self.details_class(identifier, "test", version="1.0.0")
        change = self.details_class(identifier, "test", version="1.0.1")
        original.copy_from(change)
        self.assertEqual(original.version, change.version)

    # def test_write_unique_data(self):
    #     identifier = "a" * 32
    #     original = self.details_class(identifier, "test", version="1.0.0")
    #     original.write_unique_data()

    def tearDown(self) -> None:
        crx_file_exists = os.path.exists(TEST_DOWNLOAD_PATH)
        if crx_file_exists:
            os.unlink(TEST_DOWNLOAD_PATH)
        manifest_file_exists = os.path.exists(TEST_MANIFEST_PATH)
        if manifest_file_exists:
            os.unlink(TEST_MANIFEST_PATH)

