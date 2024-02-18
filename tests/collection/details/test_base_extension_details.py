# -*- coding: utf-8 -*-
from .base_tests import BaseTests as BT
from extspider.collection.details.base_extension_details import BaseExtensionDetails
from dataclasses import astuple


class TestBaseExtensionDetails(BT.DetailsTestCase):

    @property
    def details_class(self):
        return BaseExtensionDetails

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

    def test_update_details(self):
        pass

    def test_download(self):
        pass
