# -*- coding: utf-8 -*-
from pathlib import Path
from unittest import TestCase, skip
from extspider.collection.workers import Counter
from extspider.collection.workers import CollectorWorker, DatabaseWorker
from extspider.collection.details.chrome_extension_details import ChromeExtensionDetails
from extspider.storage.extension_handle import ExtensionHandle
from extspider.common.exception import MaxRequestRetryError
from extspider.common.configuration import DB_PATH
from extspider.storage.database_handle import DatabaseHandle

DATABASE_NAME = "database.sqlite"
DATABASE_PATH = Path(DB_PATH) / DATABASE_NAME


class TestCounter(TestCase):
    def test_counter(self):
        count = Counter()
        count.increment()
        self.assertEqual(int(count), 1)
        self.assertEqual(str(count), "1")
        self.assertEqual(int(count + 2), 3)
        self.assertTrue(count > 0)
        self.assertTrue(count < 2)
        self.assertTrue(count == 1)
        with self.assertRaises(ZeroDivisionError):
            count / 0
        count.decrement()
        self.assertEqual(int(count), 0)


class TestCollectorWorker(TestCase):

    def setUp(self) -> None:
        self.collector_worker = CollectorWorker()
        self.extension_ids = [
            "eiaekkbkomopkiidlmeabjpjldhbikfc",
            "gaoijlmokigkaaocblpcmlifgipojeip"
        ]

    def test_put_queue(self):
        for extension_id in self.extension_ids:
            CollectorWorker.collect_queue.put(extension_id)

        self.assertEqual(CollectorWorker.collect_queue.qsize(),
                         len(self.extension_ids))

        for index in range(len(self.extension_ids)):
            extension_id = CollectorWorker.collect_queue.get(timeout=10)
            self.assertEqual(self.extension_ids[index],
                             extension_id)
            CollectorWorker.collect_queue.task_done()

        self.assertEqual(CollectorWorker.collect_queue.qsize(), 0)

    # TODO: 这里得想一个办法让测试能够进行且不会删除结果文件
    @skip
    def test_collect_details(self):
        # Test Existing Extensions
        for extension_id in self.extension_ids:
            CollectorWorker.collect_queue.put(extension_id)

        for _ in range(len(self.extension_ids)):
            extension_id = CollectorWorker.collect_queue.get(timeout=10)
            extension = ChromeExtensionDetails(extension_id)
            self.collector_worker.collect_details(extension)

        self.assertEqual(self.collector_worker.finished_queue.qsize(),
                         len(self.extension_ids))

        for _ in range(len(self.extension_ids)):
            chrome_extension = self.collector_worker.finished_queue.get(timeout=10)
            self.assertIsInstance(chrome_extension, ChromeExtensionDetails)
            self.assertIsNotNone(chrome_extension.identifier)
            self.assertIsNotNone(chrome_extension.version)
            self.collector_worker.finished_queue.task_done()

        # Test Bad Extension
        bad_extension_id = "a" * 32
        extension = ChromeExtensionDetails(bad_extension_id)
        is_success = self.collector_worker.collect_details(extension)
        self.assertFalse(is_success)

        self.assertEqual(self.collector_worker.finished_queue.qsize(), 0)

    @skip
    def test_download_extension(self):
        for extension_id in self.extension_ids:
            extension = ChromeExtensionDetails(extension_id)
            self.collector_worker.collect_details(extension)
            is_success = self.collector_worker.download_extension(extension)
            self.assertTrue(is_success)
            download_path = ExtensionHandle.get_extension_storage_path(
                extension.identifier,
                extension.version
            )
            self.assertTrue(Path(download_path).is_file())

        # Test no version extension
        extension = ChromeExtensionDetails(
            identifier=self.extension_ids[0],
            version=None
        )
        is_success = self.collector_worker.download_extension(extension)
        self.assertTrue(is_success)
        download_path = ExtensionHandle.get_extension_storage_path(
            extension.identifier,
            extension.version
        )
        self.assertTrue(Path(download_path).is_file())

        # Test bad none extension
        extension = ChromeExtensionDetails(
            identifier="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            version="1.0.1"
        )
        is_success = self.collector_worker.download_extension(extension)
        self.assertFalse(is_success)
        download_path = ExtensionHandle.get_extension_storage_path(
            extension.identifier,
            extension.version
        )
        self.assertFalse(Path(download_path).is_file())


@skip
class TestDatabaseWorker(TestCase):

    def setUp(self) -> None:
        DatabaseHandle.setup_engine(DATABASE_PATH)
        self.database_worker = DatabaseWorker()

    def tearDown(self) -> None:
        if DatabaseHandle.engine is not None:
            DatabaseHandle.Session.remove()
            DatabaseHandle.engine.dispose()
            DatabaseHandle.engine = None

        if Path(DATABASE_PATH).is_file():
            Path(DATABASE_PATH).unlink()

    def test_save_extension(self):
        extension = ChromeExtensionDetails("mffednhfmeflihkcikanfhpnincpkejc")
        extension.update_details()
        is_success = self.database_worker.save_extension(extension)
        self.assertTrue(is_success)
        session = DatabaseHandle.get_session()
        original_extension = DatabaseHandle.get_or_create_extension(
            session, extension.identifier, extension.version
        )
        self.assertIsNotNone(original_extension)
        self.assertIsNotNone(original_extension.name)
