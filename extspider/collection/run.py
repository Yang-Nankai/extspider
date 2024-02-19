from concurrent.futures import ThreadPoolExecutor
from extspider.collection.workers import CollectorWorker, DatabaseWorker, ProgressTrackerWorker, set_up
from extspider.common.configuration import COLLECTORS_AMOUNT, CONFIGURATION

UPDATE_SECONDS = CONFIGURATION["scraper_parameters"]["update_seconds"]


def run() -> None:
    # TODO: 这里setup肯定是不合适的，后面要改
    set_up()
    collector_workers = [CollectorWorker(collector_number + 1)
                         for collector_number in range(COLLECTORS_AMOUNT)]
    database_worker = DatabaseWorker()
    progress_tracker = ProgressTrackerWorker(update_seconds=UPDATE_SECONDS, enable_feishu=True)

    with ThreadPoolExecutor() as executor:
        executor.submit(progress_tracker.run)
        executor.submit(database_worker.run)

        for worker in collector_workers:
            executor.submit(worker.run)

        CollectorWorker.finished_event.wait()
        DatabaseWorker.finished_event.wait()
        ProgressTrackerWorker.finished_event.wait()
