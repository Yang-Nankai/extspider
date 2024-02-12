import random
from typing import Optional, ByteString
from hashlib import md5
from datetime import date
from sqlalchemy.exc import IntegrityError
from unittest import TestCase

from extspider.storage.models.common import (BaseModelTestCase,
                                                   get_random_extension_id,
                                                   TEST_RECORDS_AMOUNT)
from extspider.storage.models.archive import Archive
from extspider.storage.models.extension import Extension


class TestArchive(BaseModelTestCase, TestCase):


    @staticmethod
    def compute_digest(input:ByteString) -> str:
        return md5(input).hexdigest()


    def get_test_extension(self) -> Extension:
        with self.session.begin():
            test_extension = Extension(get_random_extension_id())
            self.session.add(test_extension)
        return test_extension


    def get_test_archive(self, extension:Optional[Extension]=None) -> Archive:
        if extension is None:
            extension = self.get_test_extension()

        with self.session.begin():
            digest = self.compute_digest("test_archive".encode())
            test_archive = Archive(digest, extension.id)
            self.session.add(test_archive)
        return test_archive


    def assertNoResults(self) -> None:
        with self.session.begin():
            results = self.session.query(Archive).all()
            self.assertEqual(results, [])


    def test_insertion(self):
        test_extension = self.get_test_extension()

        with self.session.begin():
            # Complete constructor
            for i in range(TEST_RECORDS_AMOUNT):
                test_digest = self.compute_digest(
                    f"test_digest_{i}".encode()
                )
                test_archive = Archive(
                    extension_id=test_extension.id,
                    download_date=date.today(),
                    digest=test_digest,
                    is_corrupted = random.random() < .5,
                    byte_size = 10 ** i
                )
                self.session.add(test_archive)

            # Partial constructor
            for i in range(TEST_RECORDS_AMOUNT, TEST_RECORDS_AMOUNT*2):
                test_digest = self.compute_digest(
                    f"test_digest_{i}".encode()
                )
                test_archive = Archive(test_digest, test_extension.id)
                self.session.add(test_archive)

        expected = test_extension.archives
        results = self.session.query(Archive).all()
        self.assertEqual(results, expected)
        self.assertEqual(len(results), TEST_RECORDS_AMOUNT * 2)


    def test_update(self):
        test_archive = self.get_test_archive()
        old_digest = self.compute_digest("old_digest".encode())
        new_digest = self.compute_digest("new_digest".encode())

        test_archive.digest = old_digest
        self.session.commit()

        inserted_archive = self.session.query(Archive).first()
        self.assertEqual(inserted_archive.digest, old_digest)

        test_archive.digest = new_digest
        self.session.commit()

        updated_archive = self.session.query(Archive).first()
        self.assertEqual(updated_archive.digest, new_digest)
        self.assertEqual(updated_archive.digest, inserted_archive.digest)


    def test_deletion(self):
        test_extension = Extension(get_random_extension_id())
        for i in range(TEST_RECORDS_AMOUNT):
            test_digest = self.compute_digest(f"test_digest_{i}".encode())
            test_extension.archives.append(Archive(test_digest,
                                                   test_extension.id))
        self.session.add(test_extension)
        self.session.commit()

        for archive in test_extension.archives:
            self.session.delete(archive)
        self.session.delete(test_extension)
        self.session.commit()

        fetched_extensions = self.session.query(Extension).all()
        fetched_archives = self.session.query(Archive).all()
        self.assertEqual(fetched_extensions, [])
        self.assertEqual(fetched_archives, [])



    def test_foreign_key_integrity(self):
        # Ensure ForeignKey constraint with Extensions
        with self.session.begin():
            test_extension = Extension(get_random_extension_id())
            test_digest = self.compute_digest("test_digest".encode())
            test_archive = Archive(test_digest, test_extension.id)
            self.session.add(test_extension)
            self.session.add(test_archive)

        with self.assertRaises(IntegrityError):
            with self.session.begin():
                self.session.delete(test_extension)


    def test_digest_integrity(self):
        # Ensure no duplicate digests
        with self.assertRaises(IntegrityError):
            with self.session.begin():
                test_extension = Extension(get_random_extension_id())
                test_digest = self.compute_digest("test_digest".encode())
                test_archive_original = Archive(test_digest, test_extension.id)
                test_archive_duplicate = Archive(test_digest,
                                                 test_extension.id)
                self.session.add(test_extension)
                self.session.add(test_archive_original)
                self.session.add(test_archive_duplicate)


    def test_parameter_validation(self):
        test_archive = self.get_test_archive()

        with self.session.begin():
            # Test invalid byte size
            with self.assertRaises(ValueError):
                test_archive.byte_size = 0
            with self.assertRaises(ValueError):
                test_archive.byte_size = -1


        self.assertEqual(test_archive.byte_size, None)


    def test_get_invalid_characters_from_id(self):
        accepted_id = 32 * "a"
        rejected_segment = "zzzz"
        rejected_id = accepted_id[:28] + rejected_segment
        self.assertEqual(len(rejected_id), 32)

        test_extension = self.get_test_extension()
        invalid_characters = test_extension.get_invalid_characters_from_id(
            rejected_id
        )
        self.assertEqual(invalid_characters, rejected_segment)

        invalid_characters = test_extension.get_invalid_characters_from_id(
            accepted_id
        )
        self.assertEqual(invalid_characters, "")