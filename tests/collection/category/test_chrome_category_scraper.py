# -*- coding: utf-8 -*-
import requests
from unittest import TestCase, skip
from extspider.collection.category.chrome_category_scraper import ChromeCategoryScraper

requests.packages.urllib3.disable_warnings()

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        "AppleWebKit/537.36 (KHTML, like Gecko)"
        "Chrome/118.0.5993.90"
    ),
    "Host": "chromewebstore.google.com",
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
}


class TestChromeCategoryScraper(TestCase):

    def setUp(self):
        self.scraper = ChromeCategoryScraper("productivity/communication")

    def test_request_details(self):
        details = self.scraper.request_details()
        self.assertIsNotNone(details)
        self.assertGreater(len(details), 0)

        # Given the token
        self.scraper.token = "QWJ0WnBNWm93QkIwdXl0amJkNEsxYjFzN1ZOUnJVWmhWT3VUVFRKUEFzQ1B" \
                             "kLTNiSEJEemhJNDlHbGFoNzREUmlwd1BpaFM1RXk1U3JQNVpYVFkxZ1JPVEdtSW" \
                             "41Y0lEZlpWLVJmMGVPU1NEMXR2OGpZclpXbVI3VHlXQXZRY0ZtVEJKb1VTMDNudTY1" \
                             "MHFjdVpEUXpzUDE4X1RYX2xmb2MwX0xka1p5cnNfSE1TRTBnb3Z5eXNmbVVlVWttd3" \
                             "pkNkwtTjZYeDM1RVdtbkpRVlB3VzVhcWN1dnZvT3ZwLVpOcUdzN0Myd2ZsQzZYbFN" \
                             "SQXFpSHNBZ0pTZ0xEdWUzbW5ONWx3eWdadXZlOXJnPT0="
        token_details = self.scraper.request_details()
        self.assertIsNotNone(token_details)
        self.assertGreater(len(token_details), 0)

        self.assertNotEqual(details, token_details)

        # Not exists category
        self.bad_scraper = ChromeCategoryScraper("productivity/fun")
        bad_details = self.bad_scraper.request_details()
        self.assertIsNone(bad_details)
        self.bad_scraper.ids_writter.close()

    def test_collect_and_store(self):
        details_data = self.scraper.request_details()
        self.assertGreater(len(details_data), 0)
        self.scraper.collect_and_store(details_data)
        self.assertGreater(len(self.scraper.found_ids), 0)

    def test_get_categories(self):
        categories = ChromeCategoryScraper.get_categories()
        self.assertGreater(len(categories), 0)
        for category_name in categories:
            self.assertIsInstance(category_name, str)
            self.assertGreater(len(category_name), 0)

    @skip
    def test_quick_scan(self):
        ChromeCategoryScraper.quick_scan()

    def tearDown(self) -> None:
        # close the resource
        self.scraper.ids_writter.close()

    @skip
    def test_big_run(self):
        from extspider.collection.details.chrome_extension_details import ChromeExtensionDetails
        from extspider.collection.workers import Counter
        from extspider.storage.archive_handle import ArchiveHandle
        from extspider.common.context import DATA_PATH
        from concurrent.futures import ThreadPoolExecutor
        from queue import Queue
        import csv
        import time

        class CollectorWorker:
            collection_queue: Queue[ChromeExtensionDetails] = Queue()
            error_queue: Queue[list] = Queue()
            n_failures = Counter()
            n_successes = Counter()

            def run(self):
                print("Collector started")
                while self.collection_queue.qsize() > 0:

                    try:
                        extension = self.collection_queue.get(timeout=10)
                        extension.update_details()
                        download_path = ArchiveHandle.get_extension_storage_path(
                            extension.identifier,
                            extension.version_name
                        )
                        extension.download(download_path)
                        self.n_successes.increment()
                    except Exception as error:
                        self.error_queue.put([
                            extension.identifier, extension.name,
                            extension.url_name, type(error).__name__, str(error)
                        ])
                        print(f"Collection error for {extension.identifier}")
                        print(f"{type(error).__name__}: {error}")
                        self.n_failures.increment()
                    finally:
                        DataWorker.storage_queue.put(extension)
                        self.collection_queue.task_done()

                print("Collector finished!")

        class DataWorker:
            storage_queue: Queue[ChromeExtensionDetails] = Queue()

            error_file = open(f"{DATA_PATH}/errors.csv", "a")
            error_writer = csv.writer(error_file)

            data_file = open(f"{DATA_PATH}/results.csv", "a")
            data_writer = csv.writer(data_file)

            def run(self):
                print("Storage started")
                while (CollectorWorker.collection_queue.qsize() > 0
                       or CollectorWorker.error_queue.qsize() > 0
                       or self.storage_queue.qsize() > 0):
                    if CollectorWorker.error_queue.qsize() > 0:
                        error = CollectorWorker.error_queue.get()
                        self.error_writer.writerow(error)
                        self.error_file.flush()
                        CollectorWorker.error_queue.task_done()
                    elif self.storage_queue.qsize() > 0:
                        extension = self.storage_queue.get()
                        self.data_writer.writerow(extension)
                        self.data_file.flush()
                        self.storage_queue.task_done()
                    else:
                        time.sleep(60)
                self.error_file.close()
                self.data_file.close()
                print("Storage finished!")

        class ProgressTrackerWorker:
            n_failures = CollectorWorker.n_failures
            n_successes = CollectorWorker.n_successes
            collection_queue = CollectorWorker.collection_queue
            error_queue = CollectorWorker.error_queue
            storage_queue = DataWorker.storage_queue

            def run(self):
                print("Progress tracker started")
                while (self.collection_queue.qsize() > 0
                       or self.storage_queue.qsize() > 0):
                    # os.system("clear")
                    if self.n_successes > 0:
                        failure_rate = \
                            self.n_failures / self.n_successes * 100
                    else:
                        failure_rate = "Undefined"

                    print(f"Collection: {self.collection_queue.qsize()}\n"
                          f"Storage: {self.storage_queue.qsize()}\n"
                          f"Error: {self.error_queue.qsize()}\n"
                          f"Successes/Failures: {self.n_successes}/{self.n_failures}\n"
                          f"Failure rate: {failure_rate}%"
                          )
                    time.sleep(30)
                print("Progress tracker finished!")

        ChromeCategoryScraper.quick_scan()
        print("--------------- Scan complete! ---------------")
        del ChromeCategoryScraper.found_ids
        results_length = len(ChromeCategoryScraper.results)
        print(f"Found {results_length} extensions; Preparing queue...")
        for _ in range(len(ChromeCategoryScraper.results)):
            extension = ChromeCategoryScraper.results.pop(0)
            CollectorWorker.collection_queue.put(extension)

        print("Collection queue is ready; Collection is starting...")
        parallel_threads = 8

        with ThreadPoolExecutor() as executor:
            executor.submit(DataWorker().run)
            executor.submit(ProgressTrackerWorker().run)
            for _ in range(parallel_threads):
                worker = CollectorWorker()
                executor.submit(worker.run)
            print("all jobs started")

            CollectorWorker.collection_queue.join()
            DataWorker.storage_queue.join()
