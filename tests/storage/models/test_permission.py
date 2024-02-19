import json
import sqlite3
from typing import List
from decimal import Decimal
import random
from hashlib import md5
import os
from datetime import date
from unittest import TestCase

import sqlalchemy

from extspider.common.context import TEST_SAMPLES_PATH
from extspider.storage.models.common import (BaseModelTestCase,
                                             TEST_RECORDS_AMOUNT)
from extspider.common.utils import get_random_extension_id
from extspider.storage.models.permission import ExtensionPermission

# region TEST SAMPLES INITIALISATION
SAMPLES_ROOT = os.path.join(TEST_SAMPLES_PATH, "database_handle")


class TestExtensionPermissionPermission(BaseModelTestCase, TestCase):

    def assertInvalidId(self, invalid_id: str) -> None:
        with self.assertRaises(ValueError):
            self.session.add(ExtensionPermission(invalid_id, "1.0.1"))

    def assertInvalidIds(self, invalid_id_list: List[str]) -> None:
        for invalid_id in invalid_id_list:
            self.assertInvalidId(invalid_id)

    # def assertInvalidPrimaryKeys(self) -> None:
    #     with self.assertRaises():
    def assertInvalidManifestVersion(self, invalid_manifest_version: int) -> None:
        with self.assertRaises(ValueError):
            self.session.add(ExtensionPermission(
                extension_id=get_random_extension_id(),
                extension_version="1.0.1",
                manifest_version=invalid_manifest_version
            ))

    def assertNoResults(self) -> None:
        results = self.session.query(ExtensionPermission).all()
        self.assertEqual(results, [])

    def test_insertion(self):
        expected = list()

        with self.session.begin():
            # Complete constructor
            for _ in range(TEST_RECORDS_AMOUNT):
                test_extension_permission = ExtensionPermission(
                    extension_id=get_random_extension_id(),
                    extension_version="1.0.1",
                    manifest_version=3,
                    permissions=list("Tabs"),
                    optional_permissions=list("Tabs"),
                    content_scripts_matches=list("Tabs"),
                    host_permissions=list("Tabs"),
                    optional_host_permissions=list("Tabs")
                )
                self.session.add(test_extension_permission)
                expected.append(test_extension_permission)

            # Partial constructor
            for _ in range(TEST_RECORDS_AMOUNT):
                test_extension_permission = ExtensionPermission(get_random_extension_id(), "1.0.1")
                self.session.add(test_extension_permission)
                expected.append(test_extension_permission)

        result = self.session.query(ExtensionPermission).all()
        self.assertEqual(result, expected)
        self.assertEqual(len(result), TEST_RECORDS_AMOUNT * 2)

    def test_insertion_same_id(self):
        expected = list()
        with self.session.begin():
            test_extension_id = get_random_extension_id()
            test_extension_permission_one = ExtensionPermission(test_extension_id, "1.0.0")
            self.session.add(test_extension_permission_one)
            expected.append(test_extension_permission_one)

            test_extension_permission_two = ExtensionPermission(test_extension_id, "1.0.1")
            self.session.add(test_extension_permission_two)
            expected.append(test_extension_permission_two)

        result = self.session.query(ExtensionPermission).all()
        self.assertEqual(result, expected)
        self.assertEqual(len(result), 2)

    def test_update(self):
        original_id = get_random_extension_id()
        original_version = "1.0.1"
        test_extension_permission = ExtensionPermission(original_id, original_version)
        self.session.add(test_extension_permission)
        self.session.commit()

        inserted_extension_permission = self.session.query(ExtensionPermission).first()
        self.assertEqual(inserted_extension_permission.extension_version, original_version)

        updated_version = "1.0.2"
        test_extension_permission.extension_version = "1.0.2"
        self.session.commit()

        updated_extension_permission = self.session.query(ExtensionPermission).first()
        self.assertEqual(updated_extension_permission.extension_version, updated_version)
        self.assertEqual(inserted_extension_permission.extension_version,
                         updated_extension_permission.extension_version)

    def test_deletion(self):
        test_extension_permission = ExtensionPermission(get_random_extension_id(), "1.0.1")
        self.session.add(test_extension_permission)
        self.session.commit()

        fetched_extension_permission = self.session.query(ExtensionPermission).all()
        self.assertEqual(fetched_extension_permission, [test_extension_permission])

        self.session.delete(test_extension_permission)
        self.session.commit()
        self.assertNoResults()

    def test_parameter_validation(self):
        # Test invalid IDs
        too_short_id = "abcde"
        too_long_id = "".join(["a" * 33])
        invalid_character_id = "".join(["q" * 32])
        self.assertInvalidIds([too_short_id,
                               too_long_id,
                               invalid_character_id])

        # Test invalid manifest version
        self.assertInvalidManifestVersion(-1)
        self.assertInvalidManifestVersion(4)

        self.session.commit()
        self.assertNoResults()

    def test_InvalidPrimaryKeys(self):
        with self.assertRaises(sqlalchemy.exc.IntegrityError):
            test_extension_id = get_random_extension_id()
            test_extension_permission = ExtensionPermission(test_extension_id)
            self.session.add(test_extension_permission)
            self.session.commit()
            self.assertNoResults()