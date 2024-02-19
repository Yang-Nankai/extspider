import json
from typing import List
from decimal import Decimal
import random
from hashlib import md5
import os
from datetime import date
from unittest import TestCase

from extspider.common.context import TEST_SAMPLES_PATH
from extspider.storage.models.common import (BaseModelTestCase,
                                             TEST_RECORDS_AMOUNT)
from extspider.common.utils import get_random_extension_id
from extspider.storage.models.extension import Extension, ExtensionCategory

# region TEST SAMPLES INITIALISATION
SAMPLES_ROOT = os.path.join(TEST_SAMPLES_PATH, "database_handle")


def read_sample(file_name):
    file_path = os.path.join(SAMPLES_ROOT, file_name)
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def read_json_sample(file_name):
    content_string = read_sample(file_name)
    return json.loads(content_string)


class TestExtension(BaseModelTestCase, TestCase):

    def assertInvalidId(self, invalid_id: str) -> None:
        with self.assertRaises(ValueError):
            self.session.add(Extension(invalid_id))

    def assertInvalidIds(self, invalid_id_list: List[str]) -> None:
        for invalid_id in invalid_id_list:
            self.assertInvalidId(invalid_id)

    def assertInvalidDownloadCount(self, invalid_download_count: int) -> None:
        with self.assertRaises(ValueError):
            self.session.add(Extension(
                id=get_random_extension_id(),
                download_count=invalid_download_count
            ))

    def assertInvalidRatingCount(self, invalid_rating_count: int) -> None:
        with self.assertRaises(ValueError):
            self.session.add(Extension(
                id=get_random_extension_id(),
                rating_count=invalid_rating_count
            ))

    def assertInvalidByteSize(self, invalid_byte_size: int) -> None:
        with self.assertRaises(ValueError):
            self.session.add(Extension(
                id=get_random_extension_id(),
                byte_size=invalid_byte_size
            ))

    def assertInvalidRatingAverage(
            self, invalid_rating_average: Decimal) -> Decimal:
        with self.assertRaises(ValueError):
            self.session.add(Extension(
                id=get_random_extension_id(),
                rating_average=invalid_rating_average
            ))

    def assertNoResults(self) -> None:
        results = self.session.query(Extension).all()
        self.assertEqual(results, [])

    def test_insertion(self):
        expected = list()

        with self.session.begin():
            test_category = ExtensionCategory("test_category")
            self.session.add(test_category)
            # Complete constructor
            for _ in range(TEST_RECORDS_AMOUNT):
                random_id = get_random_extension_id()
                test_extension = Extension(
                    id=random_id,
                    name="test_name",
                    developer_name="test_developer",
                    category_id=test_category.id,
                    download_count=random.randint(0, 100000),
                    rating_count=random.randint(0, 10000),
                    rating_average=random.random() * 5,
                    manifest=read_json_sample("test_manifest.json"),
                    byte_size=random.randint(0, 100000),
                    latest_version="0.1.2.34",
                    updated_at=date.today(),
                    download_date=date.today()
                )
                self.session.add(test_extension)
                expected.append(test_extension)

            # Partial constructor
            for _ in range(TEST_RECORDS_AMOUNT):
                random_id = get_random_extension_id()
                test_extension = Extension(random_id, test_category)
                self.session.add(test_extension)
                expected.append(test_extension)

        result = self.session.query(Extension).all()
        self.assertEqual(result, expected)
        self.assertEqual(len(result), TEST_RECORDS_AMOUNT * 2)

    def test_update(self):
        original_id = get_random_extension_id()
        test_extension = Extension(original_id)
        self.session.add(test_extension)
        self.session.commit()

        inserted_extension = self.session.query(Extension).first()
        self.assertEqual(inserted_extension.id, original_id)

        updated_id = get_random_extension_id()
        test_extension.id = updated_id
        self.session.commit()

        updated_extension = self.session.query(Extension).first()
        self.assertEqual(updated_extension.id, updated_id)
        self.assertEqual(inserted_extension.id, updated_extension.id)

    def test_deletion(self):
        test_extension = Extension(get_random_extension_id())
        self.session.add(test_extension)
        self.session.commit()

        fetched_extensions = self.session.query(Extension).all()
        self.assertEqual(fetched_extensions, [test_extension])

        self.session.delete(test_extension)
        self.session.commit()
        self.assertNoResults()

    # TODO: 测试是否是benchmark，更新会不会导致问题
    def test_insertion_update(self):
        # Same extension id, and update the version
        original_id = get_random_extension_id()
        original_version = "1.0.1"
        original_extension = Extension(
            extension_id=original_id,
            latest_version=original_version
        )
        self.session.merge(original_extension)
        self.session.commit()

        inserted_extension = self.session.query(Extension).first()
        self.assertEqual(inserted_extension.id, original_id)
        self.assertEqual(inserted_extension.latest_version, original_version)

        update_version = "1.0.2"
        update_extension = Extension(
            extension_id=original_id,
            latest_version=update_version
        )
        self.session.merge(update_extension)
        self.session.commit()

        updated_extension = self.session.query(Extension).first()
        self.assertEqual(updated_extension.id, original_id)
        self.assertEqual(inserted_extension.latest_version,
                         updated_extension.latest_version)
        all_results = self.session.query(Extension).all()
        self.assertEqual(len(all_results), 1)

    def test_parameter_validation(self):
        # Test invalid IDs
        too_short_id = "abcde"
        too_long_id = "".join(["a" * 33])
        invalid_character_id = "".join(["q" * 32])
        self.assertInvalidIds([too_short_id,
                               too_long_id,
                               invalid_character_id])

        # Test invalid download count
        self.assertInvalidDownloadCount(-1)

        # Test invalid rating count
        self.assertInvalidRatingCount(-1)

        # Test invalid rating percentages
        self.assertInvalidRatingAverage(-2.45)
        self.assertInvalidRatingAverage(5.01)

        self.assertInvalidByteSize(-10)

        self.session.commit()
        self.assertNoResults()
