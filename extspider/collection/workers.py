import logging
import time
import traceback
from datetime import timedelta
from logging import Logger
from abc import ABC as AbstractClass, abstractmethod
from typing import Any, List, Optional, Union, Iterator, Self
from queue import Queue, Empty as EmptyQueue
from threading import Event, Lock
from extspider.common.configuration import BACKLOG_LIMIT
from extspider.storage.archive_handle import ArchiveHandle
from extspider.storage.crx_archive import CrxArchive
from extspider.collection.details.base_extension_details import BaseExtensionDetails
from extspider.collection.details.chrome_extension_details import ChromeExtensionDetails
from extspider.common.log import get_logger, FeishuMessenger
from extspider.common.context import DATA_PATH

# TODO: 不是长久之计
scraped_queue: Queue[str] = Queue()

class Counter:

    def __init__(self, start_value: int = 0) -> None:
        self._count = start_value
        self.count_lock = Lock()

    @property
    def count(self) -> int:
        with self.count_lock:
            return self._count

    @count.setter
    def count(self, value: int) -> None:
        with self.count_lock:
            self._count = value

    def __str__(self) -> str:
        return str(self.count)

    def __int__(self) -> int:
        return self.count

    def __add__(self, other: Union[int, Self]) -> Self:
        return Counter(self.count + int(other))

    def increment(self, amount: int = 1):
        with self.count_lock:
            self._count += amount

    def decrement(self, amount: int = 1):
        with self.count_lock:
            self._count -= amount

    def __lt__(self, other: Union[int, Self]) -> bool:
        return self.count < int(other)

    def __gt__(self, other: Union[int, Self]) -> bool:
        return self.count > int(other)

    def __eq__(self, other: Union[int, Self]) -> bool:
        return self.count == int(other)

    def __truediv__(self, other: Union[int, Self]) -> float:
        if int(other) == 0:
            raise ZeroDivisionError("Division by zero")
        return self.count / int(other)


class Worker(AbstractClass):
    class_name = "abstract_worker"

    def __init__(self, worker_number: int = 1) -> None:
        self.worker_number = worker_number
        self.logger: Logger = get_logger(self.name)

    @property
    def name(self) -> str:
        return self.class_name + f"-#{self.worker_number}"

    @property
    @abstractmethod
    def is_exit_condition_reached(self) -> bool:
        """
        is_exit_condition_reached

        Returns:
            bool: True if the worker should stop, False otherwise
        """

    @abstractmethod
    def work(self, *args: Any, **kwargs: Any) -> Any:
        """
        work called by self.run -- performs an atomic operation
        """

    @abstractmethod
    def run(self) -> Any:
        """
        run cyclically reads data from a queue and forwards it to self.work
        """

    def log(self, message: str, level: int = logging.INFO):
        self.logger.log(level, message)


class CollectorWorker(Worker):
    class_name = "collector_worker"

    # collect_queue: Queue[str] = Queue()
    collect_queue = scraped_queue
    collected_details_count = Counter()
    downloaded_count = Counter()
    finished_queue: Queue[Union[BaseExtensionDetails, CrxArchive]] = Queue()

    failed_details_queue: Queue[tuple[Exception, BaseExtensionDetails]] = Queue()
    failed_details_count = Counter()
    failed_downloads_queue: Queue[tuple[Exception, BaseExtensionDetails]] = Queue()
    failed_storage_queue: Queue[tuple[Exception, str]] = Queue()

    finished_event = Event()

    def __init__(self, worker_number: int = 1) -> None:
        super().__init__(worker_number)

    @property
    def is_exit_condition_reached(self) -> bool:
        return self.collect_queue.qsize() == 0

    def enqueue_collection_error(self,
                                 error: Exception,
                                 extension_id: str) -> None:
        self.failed_details_queue.put((error, extension_id))

    def enqueue_download_error(self,
                               error: Exception,
                               extension: BaseExtensionDetails) -> None:
        self.failed_downloads_queue.put((error, extension))

    def enqueue_storage_error(self,
                              error: Exception,
                              extension_id: str) -> None:
        self.failed_storage_queue.put((error, extension_id))

    def collect_details(self,
                        extension: BaseExtensionDetails) -> bool:
        """
        collect_details scrapes details page and handles exceptions

        Args:
            extension (BaseExtensionDetails): extension to be scraped

        Returns:
            bool: True if collection was successful, False otherwise
        """
        self.log(f"Collecting {extension.identifier}...", logging.DEBUG)
        try:
            extension.update_details()
            # TODO: 这里需要review，将id+version作为唯一标识写入
            # extension.write_unique_data()

        except Exception as error:
            self.log(
                f"Encountered {type(error).__name__} upon "
                f"collecting {extension.identifier}",
                logging.ERROR
            )
            self.enqueue_collection_error(error, extension)
            traceback.print_exc()
            return False
        else:
            # print(f"Successfully collected {repr(extension.identifier)}")
            self.log(f"collected {repr(extension)}", logging.DEBUG)
            self.finished_queue.put(extension)

        return True

    def store_extension_archive(self,
                                extension_id: str,
                                download_path: Optional[str]) -> bool:

        # this is a new release; store on disk and add to database
        self.log(f"Storing {extension_id}...", logging.DEBUG)
        try:
            archive = ArchiveHandle.store_extension_archive(extension_id,
                                                            download_path)

        except Exception as error:
            self.log(f"Encountered {type(error).__name__} "
                     f"upon storing {extension_id}", logging.ERROR)
            self.enqueue_storage_error(error, extension_id)
            traceback.print_exc()
            return False

        else:
            self.finished_queue.put(archive)

        return True

    def download_extension(self, extension: BaseExtensionDetails) -> bool:
        """
        download_extension

        Args:
            extension (ScrapedExtension): extension to be downloaded

        Returns:
            bool: True if download was successful, False otherwise
        """
        # self.log(f"Downloading {extension.identifier}", logging.DEBUG)

        try:
            download_path = ArchiveHandle.get_extension_storage_path(
                extension.identifier,
                extension.version
            )
            extension.download(download_path)

        except Exception as error:
            self.log(
                f"Encountered {type(error).__name__} "
                f"upon downloading {extension.identifier}",
                logging.ERROR
            )
            self.enqueue_download_error(error, extension)
            traceback.print_exc()
            return False

    def work(self,
             extension: BaseExtensionDetails) -> None:
        if self.collect_details(extension):
            # collection successfully
            self.collected_details_count.increment()

        if self.download_extension(extension):
            # download successfully
            self.downloaded_count.increment()

    def run(self) -> int:
        print("Collector Started...")
        # TODO: 这里需要更改
        # self.set_up()
        while not self.is_exit_condition_reached:
            try:
                extension_id = self.collect_queue.get(timeout=10)
                extension = ChromeExtensionDetails(extension_id)
                self.work(extension)

            except EmptyQueue:
                continue

            except Exception as error:
                self.failed_details_queue.put([extension_id,
                                               type(error).__name__, str(error)
                                               ])
                self.log(f"Collection error for {extension_id}"
                         f"{type(error).__name__}: {error}")
                self.enqueue_collection_error(error, extension_id)
                self.log(f"{type(error).__name__}: {error}", logging.ERROR)
                traceback.print_exc()
            finally:
                # DatabaseWorker.storage_queue.put(extension)
                self.collect_queue.task_done()

        self.log("Finished", logging.INFO)
        self.finished_event.set()
        return self.worker_number


class DatabaseWorker(Worker):
    class_name = "database_worker"

    save_queue = CollectorWorker.finished_queue
    saved_extensions_count = Counter()
    # saved_archives_count = Counter()

    failed_extensions_queue: Queue[BaseExtensionDetails] = Queue()
    # failed_archives_queue: Queue[CrxArchive] = Queue()

    finished_event = Event()

    @property
    def is_exit_condition_reached(self) -> bool:
        return (CollectorWorker.finished_event.is_set()
                and self.save_queue.qsize() == 0)

    def enqueue_extension_error(self,
                                error: Exception,
                                extension: BaseExtensionDetails) -> None:
        self.failed_extensions_queue.put((error, extension))


    def save_extension(self, extension: BaseExtensionDetails) -> bool:
        try:
            # TODO: 这里思考一下需不需要添加
            extension.save_metadata()

        except Exception as error:
            self.log(f"Encountered {type(error).__name__} upon saving "
                     f"extension: {repr(extension)}", logging.ERROR)
            self.enqueue_extension_error(error, extension)
            traceback.print_exc()
            return False

        self.log(f"Saved {extension.identifier} successfully", logging.DEBUG)
        return True

    def work(self,
             metadata: Union[BaseExtensionDetails, CrxArchive]) -> None:

        # TODO: 这里原本是==，改为了instance，因为==无法检测出继承关系？
        if isinstance(metadata, BaseExtensionDetails):
            if self.save_extension(metadata):
                self.saved_extensions_count.increment()

    def run(self) -> None:
        self.log("Ready", logging.INFO)
        print("Storage Started...")
        while not self.is_exit_condition_reached:
            try:
                extension = self.save_queue.get(timeout=10)
                self.work(extension)
                self.save_queue.task_done()

            except EmptyQueue:
                continue

            except Exception as error:
                self.log(f"{type(error).__name__}: {error}", logging.ERROR)
                traceback.print_exc()

        self.log("Finished", logging.INFO)
        self.finished_event.set()


class ProgressTrackerWorker(Worker):
    class_name = "progress_tracker_worker"

    collected_details_count = CollectorWorker.collected_details_count
    downloaded_count = CollectorWorker.downloaded_count
    saved_extensions_count = DatabaseWorker.saved_extensions_count
    # saved_archives_count = DatabaseWorker.saved_archives_count

    collection_backlog = CollectorWorker.collect_queue
    database_backlog = DatabaseWorker.save_queue

    failed_details_collections = CollectorWorker.failed_details_queue
    failed_extension_downloads = CollectorWorker.failed_downloads_queue
    failed_archive_extractions = CollectorWorker.failed_storage_queue
    failed_extension_saves = DatabaseWorker.failed_extensions_queue
    # failed_archive_saves = DatabaseWorker.failed_archives_queue

    finished_event = Event()

    def __init__(self, update_seconds: int = 10, enable_feishu: bool = False) -> None:
        super().__init__()
        self.update_seconds = update_seconds
        # self.is_telegram_enabled = enable_telegram
        self.is_feishu_enabled = enable_feishu

        # TODO: 消息模块
        if self.is_feishu_enabled:
            self.messenger = FeishuMessenger()
        else:
            self.messenger = None

        self.start_time = None

    @property
    def is_exit_condition_reached(self) -> bool:
        return self.finished_event.is_set()

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self.start_time

    @property
    def elapsed_time_printable(self) -> str:
        delta = timedelta(seconds=self.elapsed_seconds)
        return str(delta).split(".")[0]  # removing microseconds

    # @property
    # def archives_per_second(self) -> Optional[float]:
    #     try:
    #         ratio = self.elapsed_seconds / self.saved_archives_count.count
    #     except ZeroDivisionError:
    #         return None
    #     return round(ratio, 2)

    @property
    def progress_status(self) -> str:
        if not self.is_exit_condition_reached:
            return "in progress..."
        else:
            return "complete!"

    @property
    def overall_status(self) -> str:
        return (
            f"-- Scraping {self.progress_status} --\n"
            f"Scraped extension details: {self.collected_details_count}\n"
            f"Saved extension metadata: {self.saved_extensions_count}\n"
            f"Downloaded crx files: {self.downloaded_count}\n"
            "-- Backlog --\n"
            f"Backlog limit: {BACKLOG_LIMIT}\n"
            f"Collection backlog: {self.collection_backlog.qsize()}\n"
            f"Database backlog: {self.database_backlog.qsize()}\n"
            "-- Failures --\n"
            f"Details collection: {self.failed_details_collections.qsize()}\n"
            f"Extension download: {self.failed_extension_downloads.qsize()}\n"
            f"Extension metadata save: {self.failed_extension_saves.qsize()}\n"
            f"-- Runtime metrics --\n"
            f"Elapsed time: {self.elapsed_time_printable}\n"
            # f"Average scrape-to-save time: {self.archives_per_second} seconds"
        )

    def send_status_update(self) -> None:
        # print(self.elapsed_time_printable)
        # print(self.archives_per_second)
        status = self.overall_status
        print(status)

        if self.is_feishu_enabled:
            self.messenger.send_message(status)

    def work(self) -> None:
        if DatabaseWorker.finished_event.is_set():
            self.finished_event.set()

        self.send_status_update()

    def run(self) -> None:
        self.start_time = time.time()
        self.log("Ready", logging.INFO)
        while not self.is_exit_condition_reached:
            try:
                self.work()
            except Exception as error:
                self.log(f"{type(error).__name__}: {error}", logging.ERROR)
                traceback.print_exc()
            finally:
                time.sleep(self.update_seconds)

        self.send_status_update()
        self.log("Finished", logging.INFO)


# TODO: 这里需要更改逻辑
def set_up() -> None:
    """
    Import all crawled extension ids into the queue
    """
    extension_ids_path = f'{DATA_PATH}/extension_ids.txt'

    with open(extension_ids_path, 'r') as file:
        for line in file:
            scraped_queue.put(line.strip())
