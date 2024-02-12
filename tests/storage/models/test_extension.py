from typing import List
from decimal import Decimal
import random
from hashlib import md5
from datetime import date
from unittest import TestCase

from extspider.storage.models.common import (BaseModelTestCase,
                                                   get_random_extension_id,
                                                   TEST_RECORDS_AMOUNT)
from extspider.storage.models.extension import Extension, ExtensionCategory
from extspider.storage.models.archive import Archive


class TestExtension(BaseModelTestCase, TestCase):

    def assertInvalidId(self, invalid_id:str) -> None:
        with self.assertRaises(ValueError):
            self.session.add(Extension(invalid_id))


    def assertInvalidIds(self, invalid_id_list:List[str]) -> None:
        for invalid_id in invalid_id_list:
            self.assertInvalidId(invalid_id)


    def assertInvalidDownloadCount(self, invalid_download_count:int) -> None:
        with self.assertRaises(ValueError):
            self.session.add(Extension(
                id=get_random_extension_id(),
                download_count=invalid_download_count
            ))


    def assertInvalidRatingCount(self, invalid_rating_count:int) -> None:
        with self.assertRaises(ValueError):
            self.session.add(Extension(
                id=get_random_extension_id(),
                rating_count=invalid_rating_count
            ))


    def assertInvalidRatingPercentage(
            self, invalid_rating_percentage:Decimal) -> Decimal:
        with self.assertRaises(ValueError):
            self.session.add(Extension(
                id=get_random_extension_id(),
                rating_percentage=invalid_rating_percentage
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
                    category_id = test_category.id,
                    download_count=random.randint(0, 100000),
                    rating_count=random.randint(0, 10000),
                    rating_percentage=random.random() * 80 + 20,
                    latest_version="0.1.2.34",
                    updated_at=date.today()
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
        self.assertInvalidRatingPercentage(-19.99)
        self.assertInvalidRatingPercentage(100.01)

        self.session.commit()
        self.assertNoResults()


    def test_archive_accessibility(self):
        test_extension = Extension(get_random_extension_id())
        for i in range(TEST_RECORDS_AMOUNT):
            test_digest = md5(f"test_digest_{i}".encode()).hexdigest()
            test_archive = Archive(test_digest, test_extension.id)
            test_extension.archives.append(test_archive)

        with self.session.begin():
            self.session.add(test_extension)

        expected = test_extension.archives
        results = self.session.query(Archive).all()
        self.session.commit()

        self.assertEqual(results, expected)


    def test_five_star_rating(self):
        star_percentage_ratings = [(1, 20),
                                   (2.5, 50),
                                   (5, 100)]

        for star_rating, percentage_rating in star_percentage_ratings:
            test_extension = Extension(id=get_random_extension_id(),
                                       rating_percentage=percentage_rating)
            self.assertEqual(test_extension.rating_stars, star_rating)


