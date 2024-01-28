# -*- coding: utf-8 -*-
from unittest import TestCase
from datetime import date
from extspider.collection.details.base_extension_details import BaseExtensionDetails
from dataclasses import asdict


class BaseTests:
    class DetailsTestCase(TestCase):

        @property
        def details_class(self):
            raise NotImplementedError


        def get_test_details(
                self,
                identifier="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        ) -> BaseExtensionDetails:
            return self.details_class(
                identifier=identifier,
                name="Sample Extension",
                version="1.0.0",
                last_update=date.today(),
                description="A sample extension",
                category="Utility",
                rating_average=4.5,
                rating_count=100,
                user_count=1000,
                manifest={"version": "1.0.0",
                          "permissions": ["storage", "activeTab"]},
                byte_size=1024,
                developer_name="Sample Developer",
                recommended_extensions=["bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                                        "cccccccccccccccccccccccccccccccc"],
                reviews={"Luna": "This is very good extension."}
            )


        def test_missing_identifier(self):
            with self.assertRaises(TypeError):
                metadata = self.details_class()


        def test_copy(self):
            original = self.get_test_details()
            copied = original.copy()

            self.assertEqual(asdict(copied), asdict(original))

            # Test for deep copy
            original.manifest["permissions"].append("new_permission")
            self.assertNotEqual(original.manifest, copied.manifest)

            original.recommended_extensions.append(
                "cccccccccccccccccccccccccccccccc"
            )
            self.assertNotEqual(original.recommended_extensions, copied.recommended_extensions)

            # Ensuring that non-mutable fields are copied correctly
            self.assertEqual(original.name, copied.name)


        def test_tuple(self):
            """Check if the tuple() function works"""
            identifier = "a" * 32
            original = self.details_class(identifier, "test")
            copied = self.details_class(identifier, "test")

            original_tuple = tuple(original)
            copied_tuple = tuple(copied)

            for og_attr, cp_attr in zip(original_tuple, copied_tuple):
                self.assertEqual(og_attr, cp_attr)


        def test_equals(self):
            """Check if the `==` operator works"""
            identifier = "a" * 32

            original = self.details_class(identifier, "test", version="1.0.0")
            copided = self.details_class(identifier, "test", version="1.0.0")
            different = self.details_class(identifier, "test", version="2.0.0")

            self.assertEqual(original, copided)
            self.assertNotEqual(original, different)


        def test_hash(self):
            """Check if the hash() function works"""
            identifier = "a" * 32

            original = self.details_class(identifier)
            copied = self.details_class(identifier)
            different = self.details_class("b" * 32)

            original_hash = hash(original)
            copied_hash = hash(copied)
            different_hash = hash(different)

            self.assertEqual(original_hash, copied_hash)
            self.assertNotEqual(original_hash, different_hash)


        def test_download(self):
            raise NotImplementedError


        def test_update_details(self):
            raise NotImplementedError
