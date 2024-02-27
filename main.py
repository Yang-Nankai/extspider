# -*- coding: utf-8 -*-
import os
from datetime import datetime

from tests.collection.category.test_chrome_category_scraper import TestChromeCategoryScraper
from extspider.storage.extension_handle import ExtensionHandle
from extspider.collection.details.chrome_extension_details import ChromeExtensionDetails
from extspider.collection.category.chrome_category_scraper import ChromeCategoryScraper
from extspider.collection.run import run
from extspider.common.context import DATA_PATH


def rename_extension_ids_file():
    current_date = datetime.datetime.now().strftime("%Y_%m_%d")
    original_filename = f"{DATA_PATH}/extension_ids.txt"
    new_filename = f"{DATA_PATH}/{current_date}_{original_filename}"
    os.rename(original_filename, new_filename)


if __name__ == '__main__':
    # 1. 首先快速爬取所有的extension_id, 生成extension_ids.txt文件
    if not os.path.exists(f"{DATA_PATH}/extension_ids.txt"):
        ChromeCategoryScraper.quick_scan()
    # 2. 然后获取所有extension的细节，并下载crx文件，同时在数据库中存放信息
    run()
    # 3. 然后将extension_ids.txt存档，改为 日期_extension_ids.txt
    rename_extension_ids_file()
