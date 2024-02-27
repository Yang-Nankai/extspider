# -*- coding: utf-8 -*-
import unittest
import os
from tempfile import TemporaryDirectory
from extspider.collection.progress_saver import ChromeProgressSaver, ProgressStatus


class TestChromeProgressSaver(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.temp_dir_path = self.temp_dir.name
        self.progress_saver = ChromeProgressSaver()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_and_load_progress(self):
        # Test Uncompleted
        scraped_categories = ["category1", "category2"]
        now_category = "test_category"
        token = "test_token"

        # Save progress
        self.progress_saver.save_uncompleted_progress(
            scraped_categories=scraped_categories,
            now_category=now_category,
            token=token
        )

        # Load progress
        loaded_progress = self.progress_saver.progress_info

        # Assert statements
        self.assertIsNotNone(loaded_progress)
        self.assertEqual(loaded_progress.get("status"), 0)
        self.assertEqual(loaded_progress.get("scraped_categories"), scraped_categories)
        self.assertEqual(loaded_progress.get("now_category"), now_category)
        self.assertEqual(loaded_progress.get("token"), token)
        # Test is_finished
        is_finished = self.progress_saver.is_finished
        self.assertFalse(is_finished)

        # Save completed progress
        self.progress_saver.save_completed_progress()

        # Load progress
        loaded_progress = self.progress_saver.progress_info
        # Assert statements
        self.assertIsNotNone(loaded_progress)
        self.assertEqual(loaded_progress.get("status"), 1)
        self.assertIsInstance(loaded_progress.get("scraped_categories"), list)

        # Test is_finished
        is_finished = self.progress_saver.is_finished
        self.assertTrue(is_finished)

    def test_load_nonexistent_progress(self):
        # Attempt to load progress from a non-existent file
        self.bad_progress_saver = ChromeProgressSaver(filename="test_progress.json")
        loaded_progress = self.bad_progress_saver.progress_info

        # Assert statement
        self.assertIsNone(loaded_progress)

        # Test is_finished
        is_finished = self.bad_progress_saver.is_finished
        self.assertTrue(is_finished)
