from concurrent.futures import ThreadPoolExecutor
from extspider.collection.workers import CollectorWorker, DatabaseWorker, ProgressTrackerWorker
from extspider.common.configuration import COLLECTORS_AMOUNT, UPDATE_SECONDS, IS_FEISHU_ENABLED
from extspider.common.context import DAILY_IDENTIFIERS_PATH
from extspider.collection.category.chrome_category_scraper import ChromeCategoryScraper


def set_up():
    """
    Import all crawled extension ids into the queue
    """
    if not DAILY_IDENTIFIERS_PATH.is_file():
        ChromeCategoryScraper.quick_scan()

    with open(DAILY_IDENTIFIERS_PATH, 'r') as file:
        for line in file:
            CollectorWorker.collect_queue.put(line.strip())


def run():
    set_up()
    collector_workers = [CollectorWorker(collector_number + 1)
                         for collector_number in range(COLLECTORS_AMOUNT)]
    database_worker = DatabaseWorker()
    progress_tracker = ProgressTrackerWorker(update_seconds=UPDATE_SECONDS,
                                             enable_feishu=IS_FEISHU_ENABLED)

    with ThreadPoolExecutor() as executor:
        executor.submit(progress_tracker.run)
        executor.submit(database_worker.run)

        for worker in collector_workers:
            executor.submit(worker.run)

        CollectorWorker.finished_event.wait()
        DatabaseWorker.finished_event.wait()
        ProgressTrackerWorker.finished_event.wait()
