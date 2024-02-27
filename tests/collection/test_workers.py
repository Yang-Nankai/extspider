# -*- coding: utf-8 -*-
from unittest import TestCase
from extspider.collection.workers import Counter
from extspider.collection.workers import CollectorWorker
from extspider.collection.details.chrome_extension_details import ChromeExtensionDetails


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
            "aoogfbnigmjindidkbijnkccpdloijfg",
            "apebhplgeobjibklnjlmjmdhfolminmh"
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

    def test_download_extension(self):
        pass