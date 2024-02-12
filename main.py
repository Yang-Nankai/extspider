# -*- coding: utf-8 -*-
from tests.collection.category.test_chrome_category_scraper import TestChromeCategoryScraper
from extspider.storage.archive_handle import ArchiveHandle

if __name__ == '__main__':
    # TestChromeCategoryScraper.test_big_run()
    identifier = "a" * 32
    version_name = "1.0.1"
    download_path = ArchiveHandle.get_extension_storage_path(
        (identifier +
         f".{version_name}.crx")
    )
    print(download_path)