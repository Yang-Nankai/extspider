# -*- coding: utf-8 -*-
import unittest
import os
from tempfile import TemporaryDirectory
from extspider.collection.progress_saver import ChromeProgressSaver


class TestChromeProgressSaver(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.temp_dir_path = self.temp_dir.name
        self.progress_saver = ChromeProgressSaver()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_load_progress(self):
        # Test Uncompleted
        status = 0
        scraped_categories = ["category1", "category2"]
        now_category = "current_category"
        token = "test_token"
        break_reason = "testing_break"

        # Save progress
        self.progress_saver.save_progress(
            status=status,
            scraped_categories=scraped_categories,
            now_category=now_category,
            token=token,
            break_reason=break_reason
        )

        # Load progress
        loaded_progress = self.progress_saver.load_progress()

        # Assert statements
        self.assertIsNotNone(loaded_progress)
        self.assertEqual(loaded_progress.get("status"), status)
        self.assertEqual(loaded_progress.get("scraped_categories"), scraped_categories)
        self.assertEqual(loaded_progress.get("now_category"), now_category)
        self.assertEqual(loaded_progress.get("token"), token)
        self.assertEqual(loaded_progress.get("break_reason"), break_reason)

        # Test Completed
        status = 1

        # Save progress
        self.progress_saver.save_progress(status=status)

        # Load progress
        loaded_progress = self.progress_saver.load_progress()
        # Assert statements
        self.assertIsNotNone(loaded_progress)
        self.assertEqual(loaded_progress.get("status"), status)
        self.assertIsInstance(loaded_progress.get("scraped_categories"), list)

    def test_load_nonexistent_progress(self):
        # Attempt to load progress from a non-existent file
        self.bad_progress_saver = ChromeProgressSaver(filename="test_progress.json")
        loaded_progress = self.bad_progress_saver.load_progress()

        # Assert statement
        self.assertIsNone(loaded_progress)

