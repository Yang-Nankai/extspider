# -*- coding: utf-8 -*-
import json
import re
import requests
import sys
from extspider.common.context import DATA_PATH
from extspider.collection.category.base_category_scraper import BaseCategoryScraper
from extspider.common.exception import CategoryCollectionError, CategoryRequestError, InvalidCategoryResponse
from extspider.collection.parsers.chrome_parser import ChromeCategoryResponseMapper
from extspider.collection.progress_saver import ChromeProgressSaver
from extspider.common.utils import request_retry_with_backoff
from extspider.common.configuration import CHROME_CATEGORY_REQUEST_ID
from typing import Dict, List
from extspider.collection.progress_saver import ProgressStatus
from extspider.common.configuration import HTTP_HEADERS

requests.packages.urllib3.disable_warnings()

CATEGORY_NAMES_PATTERN = re.compile(r',\\\"([a-z_]+/[a-z_]+)\\\"')
DETAILS_PATTERN = re.compile(r'(\[\[.*\]\])')


BASE_URL = "https://chromewebstore.google.com"
BASE_SOURCE_PATH = "category/extensions/{category}"
BASE_REQUEST_URL = BASE_URL + "/_/ChromeWebStoreConsumerFeUi/data/batchexecute"


class ChromeCategoryScraper(BaseCategoryScraper):
    # TODO: Support proxy
    # results = list()
    found_ids = set()
    scraped_categories = list()

    # TODO: 这里针对token这里有点不好看需要改正
    def __init__(self, category_name: str, token: str = "") -> None:
        self.category_name = category_name
        self.source_path = BASE_SOURCE_PATH.format(category=category_name)
        self.once_num = 64  # Num of once request extensions
        self.token = token
        self.request_id = CHROME_CATEGORY_REQUEST_ID
        self.target_url = f"{BASE_REQUEST_URL}?rpcids={self.request_id}&source-path={self.source_path}"
        # TODO: 不需要考虑文件名，因为这里只用作快速爬取的操作，而对比需要id+version，因此要在其他模块单独存储当日的数据方便对比(JSON/CSV)
        # TODO: 但是这里是追加模式，因此需要考虑一个新的方式，例如在开头加上当前时间，对于后面爬取的也这么做
        # TODO: 考虑将这个做为一个配置使用
        self.ids_writter = open(f"{DATA_PATH}/extension_ids.txt", "a", encoding='utf-8')

    @property
    def request_body(self) -> Dict:
        return {
            "f.req": f'[[["{self.request_id}","[[null,[[3,\\"{self.category_name}\\",null,null,'
                     f'2,[{self.once_num},\\"{self.token}\\"]]]]]",null,"generic"]]]'
        }

    @property
    def get_token(self) -> str:
        return self.token

    def start(self):
        # TODO: 改为Logger记录
        print(f'Starting collect category: {self.category_name} ...')
        index = 0

        while True:
            index += 1
            print(f"Cycle: {index}")

            details_data = self.request_details()
            if not all([self.token, details_data, len(details_data) > 0]):
                break
            self.collect_and_store(details_data)

        print(f"Finished collecting {self.category_name}!")
        self.ids_writter.close()

    def collect_and_store(self, data_list):
        for row in data_list:
            extension_id = row[0][0]

            if extension_id not in self.found_ids:
                self.ids_writter.write(str(extension_id + '\n'))
                self.found_ids.add(extension_id)

    @request_retry_with_backoff(max_retries=5, retry_interval=2)
    def request_details(self) -> list[str]:
        # TODO: 函数过长，逻辑过于混乱，需要清理(将request的内容单独领出来，取个好名字)
        response = requests.post(url=self.target_url,
                                 headers=HTTP_HEADERS,
                                 data=self.request_body)
        if response.status_code != 200:
            raise CategoryRequestError
        details_data = self._response_text_to_details_list(response.text)
        processed_data = ChromeCategoryResponseMapper.map_data_list(details_data)
        # Replace '=' with Unicode '\u003d' for proper encoding
        self.token = processed_data[1]
        return processed_data[0]

    @classmethod
    def get_categories(cls) -> list[str]:
        response = requests.get(BASE_URL)
        if response.status_code != 200:
            raise CategoryCollectionError(response.reason)
        html = response.text
        return cls._get_category_names_from_html(html)

    @staticmethod
    def _response_text_to_details_list(response_text: str) -> List:
        details_match = re.findall(DETAILS_PATTERN, response_text)

        if details_match:
            details = json.loads(json.loads(details_match[0])[0][2])
            return details
        else:
            raise InvalidCategoryResponse

    @staticmethod
    def _get_category_names_from_html(html) -> list[str]:
        """Extracts a list of extension category names from an HTML page"""
        return CATEGORY_NAMES_PATTERN.findall(html)

    @classmethod
    def quick_scan(cls) -> None:
        # TODO: 这里加上就不删除了，对于download就必要添加progress了，直接在日志中记录
        # TODO: 这里做一个网络连接的装饰器
        progress = ChromeProgressSaver()
        progress_info = progress.progress_info

        if not progress.is_finished:
            cls.scraped_categories = progress_info.get("scraped_categories")
            cls.resume_uncompleted_scan(progress_info)

        cls.start_new_scans()

        progress.save_progress(ProgressStatus.COMPLETED.value)

    @classmethod
    def scan_one_category(cls, category_name: str, last_token: str = ""):
        scraper = ChromeCategoryScraper(category_name, last_token)
        try:
            scraper.start()
            cls.scraped_categories.append(category_name)
        except Exception as e:
            cls.handle_scraping_error(category_name, scraper.get_token, e)

    @classmethod
    def resume_uncompleted_scan(cls, progress: Dict) -> None:
        now_category = progress.get("now_category")
        break_reason = progress.get("break_reason")
        last_token = progress.get("token")

        # TODO: 改为Logger来进行
        print("Last break reason: ", break_reason)

        cls.scan_one_category(now_category, last_token)

    @classmethod
    def start_new_scans(cls) -> None:
        all_categories = cls.get_categories()
        unscraped_categories = set(all_categories) - set(cls.scraped_categories)

        for unscraped_category in unscraped_categories:
            cls.scan_one_category(unscraped_category)

    def handle_scraping_error(self, category_name: str, break_token: str, error: Exception) -> None:
        # Handle or log the scraping error as needed
        # TODO: 改为Logger
        print(f"Error scraping category '{category_name}': {error}")
        progress_info = ChromeProgressSaver()
        # TODO: 对于save_progress的参数是否有点多？改为类的成员，后面再看
        progress_info.save_progress(ProgressStatus.UNCOMPLETED.value, self.scraped_categories, category_name,
                                    break_token, str(error))
        sys.exit()
