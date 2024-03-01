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
from extspider.storage.extension_handle import ExtensionHandle
from extspider.storage.crx_archive import CrxArchive
from extspider.collection.details.base_extension_details import BaseExtensionDetails
from extspider.collection.details.chrome_extension_details import ChromeExtensionDetails
from extspider.common.log import get_logger, FeishuMessenger
from extspider.common.context import DATA_PATH


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

    collect_queue: Queue[str] = Queue()
    collected_details_count = Counter()
    downloaded_count = Counter()
    # TODO: 这里对于finished_queue表示存疑
    finished_queue: Queue[BaseExtensionDetails] = Queue()

    failed_details_queue: Queue[tuple[Exception, BaseExtensionDetails]] = Queue()
    failed_downloads_queue: Queue[tuple[Exception, BaseExtensionDetails]] = Queue()

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
            is_updated = extension.update_details()
            if is_updated:
                # TODO: 先将记录permission的逻辑放在这里
                extension.output_permission()

        except Exception as error:
            self.log(
                f"Encountered {type(error).__name__} upon "
                f"collecting {extension.identifier}",
                logging.ERROR
            )
            self.enqueue_collection_error(error, extension.identifier)
            traceback.print_exc()
            return False
        else:
            # self.log(f"Successfully collected {extension.identifier}", logging.DEBUG)
            self.finished_queue.put(extension)

        return True

    def download_extension(self, extension: BaseExtensionDetails) -> bool:
        """
        download_extension

        Args:
            extension (ScrapedExtension): extension to be downloaded

        Returns:
            bool: True if download was successful, False otherwise
        """

        try:
            download_path = ExtensionHandle.get_extension_storage_path(
                extension.identifier,
                extension.version
            )
            extension.download(download_path)
            # TODO: 将load_manifest从download逻辑中转移出来了，这下不会出现问题
            #  但是这里做的事情太多了，需要refactor&review
            extension.load_manifest(download_path)

        except Exception as error:
            # TODO: 添加中括号让到时候针对错误的能够快速定位
            self.log(
                f"Encountered {type(error).__name__} "
                f"upon downloading {[extension.identifier]}",
                logging.ERROR
            )
            self.enqueue_download_error(error, extension)
            traceback.print_exc()
            return False
        else:
            self.log(f"Successfully downloaded {repr(extension)}", logging.DEBUG)

        return True

    def work(self,
             extension: BaseExtensionDetails) -> None:
        if self.collect_details(extension):
            # collection successfully
            self.collected_details_count.increment()

        if self.download_extension(extension):
            # download successfully
            self.downloaded_count.increment()

    def run(self) -> int:
        self.log(f"{self.name} is ready and run...", logging.INFO)
        while not self.is_exit_condition_reached:
            try:
                extension_id = self.collect_queue.get(timeout=10)
                extension = ChromeExtensionDetails(extension_id)
                self.work(extension)

            except EmptyQueue:
                continue

            except Exception as error:
                self.log(f"{type(error).__name__}: {error}", logging.ERROR)
                traceback.print_exc()

            finally:
                self.collect_queue.task_done()

        self.log("Finished", logging.INFO)
        self.finished_event.set()

        return self.worker_number


class DatabaseWorker(Worker):
    class_name = "database_worker"

    save_queue = CollectorWorker.finished_queue
    saved_extensions_count = Counter()

    failed_extensions_queue: Queue[BaseExtensionDetails] = Queue()

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
             metadata: BaseExtensionDetails) -> None:

        if isinstance(metadata, BaseExtensionDetails):
            if self.save_extension(metadata):
                self.saved_extensions_count.increment()

    def run(self) -> None:
        self.log(f"{self.name} is ready and run...", logging.INFO)
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

    collection_backlog = CollectorWorker.collect_queue
    database_backlog = DatabaseWorker.save_queue

    failed_details_collections = CollectorWorker.failed_details_queue
    failed_extension_downloads = CollectorWorker.failed_downloads_queue
    failed_extension_saves = DatabaseWorker.failed_extensions_queue

    finished_event = Event()

    def __init__(self, update_seconds: int = 10, enable_feishu: bool = False) -> None:
        super().__init__()
        self.update_seconds = update_seconds
        self.is_feishu_enabled = enable_feishu

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

    @property
    def progress_status(self) -> str:
        if not self.is_exit_condition_reached:
            return "in progress..."
        else:
            return "complete!"

    @property
    def overall_status(self) -> str:
        return (
            f"[Status]: {self.progress_status}\n"
            f"[ScrapedExtensionDetails]: {self.collected_details_count}\n"
            f"[SavedExtensionMetadata]: {self.saved_extensions_count}\n"
            f"[DownloadedExtensionCrx]: {self.downloaded_count}\n"
            "- Backlog\n"
            f"[BacklogLimit]: {BACKLOG_LIMIT}\n"
            f"[CollectionBacklog]: {self.collection_backlog.qsize()}\n"
            f"[DatabaseBacklog]: {self.database_backlog.qsize()}\n"
            "- Failures\n"
            f"[DetailsCollection]: {self.failed_details_collections.qsize()}\n"
            f"[ExtensionDownload]: {self.failed_extension_downloads.qsize()}\n"
            f"[ExtensionMetadataSave]: {self.failed_extension_saves.qsize()}\n"
            f"- Runtime metrics\n"
            f"[ElapsedTime]: {self.elapsed_time_printable}\n"
        )

    def send_status_update(self) -> None:
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
        self.log(f"{self.name} is ready and run...", logging.INFO)
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

