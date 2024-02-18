# -*- coding: utf-8 -*-
import os.path
from unittest import TestCase
from extspider.collection.workers import CollectorWorker, DatabaseWorker, set_up
from extspider.collection.details.chrome_extension_details import ChromeExtensionDetails
from extspider.storage.archive_handle import ArchiveHandle


class TestCollectorWorker(TestCase):
    def setUp(self) -> None:
        self.collector = CollectorWorker()
        set_up()

    def test_setup(self):
        self.assertGreater(self.collector.collect_queue.qsize(), 0)
        extension_id = self.collector.collect_queue.get(timeout=10)
        self.assertIsNotNone(extension_id)
        self.assertIsInstance(extension_id, str)
        next_extension_id = self.collector.collect_queue.get(timeout=10)
        self.assertIsNotNone(next_extension_id)
        self.assertIsInstance(next_extension_id, str)
        self.assertNotEqual(extension_id, next_extension_id)

    def test_work(self):
        extension_id = self.collector.collect_queue.get(timeout=10)
        self.assertIsNotNone(extension_id)
        extension = ChromeExtensionDetails(extension_id)

        self.collector.work(extension)
        extension = self.collector.finished_queue.get(timeout=10)
        self.assertIsNotNone(extension)
        self.assertIsNotNone(extension.manifest)

        download_path = ArchiveHandle.get_extension_storage_path(
            extension.identifier,
            extension.version
        )
        self.assertTrue(os.path.exists(download_path))
        # remove the data
        os.remove(download_path)


class TestDatabaseWorker(TestCase):

    def setUp(self) -> None:
        self.collector = CollectorWorker()
        set_up()
        extension_id = self.collector.collect_queue.get(timeout=10)
        extension = ChromeExtensionDetails(extension_id)
        self.collector.work(extension)

    def test_run(self):
        database_worker = DatabaseWorker()
        extension = database_worker.save_queue.get(timeout=10)
        database_worker.work(extension)
        self.assertEqual(database_worker.saved_extensions_count.count, 1)
        database_worker.save_queue.task_done()
        self.assertTrue(database_worker.save_queue.empty())
        download_path = ArchiveHandle.get_extension_storage_path(
            extension.identifier,
            extension.version
        )
        # remove the data
        os.remove(download_path)