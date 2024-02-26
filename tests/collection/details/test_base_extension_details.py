# -*- coding: utf-8 -*-
import os.path
from .base_tests import BaseTests as BT
from extspider.collection.details.base_extension_details import BaseExtensionDetails
from extspider.common.context import DATA_PATH
from dataclasses import astuple
from extspider.common.exception import InvalidExtensionIdentifier
DOWNLOAD_PATH = os.path.join(DATA_PATH, "a"*32)


class TestBaseExtensionDetails(BT.DetailsTestCase):

    @property
    def details_class(self):
        return BaseExtensionDetails

    def test_identifier(self):
        correct_identifier = "a" * 32
        extension = BaseExtensionDetails(correct_identifier)

        wrong_identifier = "a" * 33
        with self.assertRaises(InvalidExtensionIdentifier):
            extension = BaseExtensionDetails(wrong_identifier)

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

    def test_download(self):
        with self.assertRaises(NotImplementedError):
            original = self.get_test_details()
            original.download(DOWNLOAD_PATH)

    def test_update_details(self):
        with self.assertRaises(NotImplementedError):
            original = self.get_test_details()
            original.update_details()


