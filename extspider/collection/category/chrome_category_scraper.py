# -*- coding: utf-8 -*-
import json
import re
import requests
import sys
from typing import Dict, List, Optional
from extspider.common.context import DATA_PATH
from extspider.collection.category.base_category_scraper import BaseCategoryScraper
from extspider.common.exception import (CategoryRequestTypesError, CategoryRequestDetailsError,
                                        InvalidCategoryResponseFormat, RequestError)
from extspider.collection.parsers.chrome_parser import ChromeCategoryResponseMapper
from extspider.collection.progress_saver import ChromeProgressSaver
from extspider.common.utils import request_retry_with_backoff
from extspider.common.configuration import (CHROME_CATEGORY_REQUEST_ID,
                                            PROXIES, HTTP_HEADERS,
                                            CHROME_SCRAPER_ONCE_NUM)
from requests.exceptions import RequestException
from extspider.common.log import get_logger
from logging import Logger
requests.packages.urllib3.disable_warnings()


CATEGORY_NAMES_PATTERN = re.compile(r',\\\"([a-z_]+/[a-z_]+)\\\"')
DETAILS_PATTERN = re.compile(r'(\[\[.*\]\])')

BASE_URL = "https://chromewebstore.google.com"
BASE_SOURCE_PATH = "category/extensions/{category}"
BASE_REQUEST_URL = BASE_URL + "/_/ChromeWebStoreConsumerFeUi/data/batchexecute"


class ChromeCategoryScraper(BaseCategoryScraper):
    # results = list()
    found_ids = set()
    scraped_categories = list()

    def __init__(self, category_name: str, token: str = "") -> None:
        self.category_name = category_name
        self.source_path = BASE_SOURCE_PATH.format(category=category_name)
        self.once_num = CHROME_SCRAPER_ONCE_NUM
        self.token = token
        self.request_id = CHROME_CATEGORY_REQUEST_ID
        self.target_url = f"{BASE_REQUEST_URL}?rpcids={self.request_id}" \
                          f"&source-path={self.source_path}"
        self.ids_writter = open(f"{DATA_PATH}/extension_ids.txt", "a", encoding='utf-8')
        # TODO: 同时这里"extension_id":"verison" 这种结果需要放在detail代码中，并添加进度条的内容???
        # TODO: 日志处理这块，看完B站视频之后再处理
        # self.logger: Logger = get_logger("Chrome_category_scraper")

    @property
    def request_body(self) -> Dict:
        return {
            "f.req": f'[[["{self.request_id}","[[null,[[3,\\"{self.category_name}\\",null,'
                     f'null,2,[{self.once_num},\\"{self.token}\\"]]]]]",null,"generic"]]]'
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

            details_data = self.request_simple_details()
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

    def update_token_and_get_details_list(self, details_data: List[str]):
        processed_data = ChromeCategoryResponseMapper.map_data_list(details_data)
        # Replace '=' with Unicode '\u003d' for proper encoding
        self.token = processed_data[1]
        return processed_data[0]

    @request_retry_with_backoff(max_retries=5, retry_interval=2)
    def request_simple_details(self) -> Optional[List[str]]:
        response = requests.post(url=self.target_url,
                                 headers=HTTP_HEADERS,
                                 data=self.request_body,
                                 proxies=PROXIES)
        if response.status_code != 200:
            raise CategoryRequestDetailsError(f"response status code is {response.status_code}")

        details_data = self._details_response_to_json_format(response.text)
        details_list = self.update_token_and_get_details_list(details_data)

        return details_list

    @classmethod
    def get_categories(cls) -> list[str]:
        response = requests.get(url=BASE_URL,
                                proxies=PROXIES)
        if response.status_code != 200:
            raise CategoryRequestTypesError(f"response status code is {response.status_code}")
        html_ = response.text
        return cls._get_category_names_from_html(html_)

    @staticmethod
    def _details_response_to_json_format(response_text: str) -> List:
        """Remove irrelevant content from the response and convert it
        into List type data using the JSON library."""
        details_match = re.findall(DETAILS_PATTERN, response_text)

        if details_match:
            details = json.loads(json.loads(details_match[0])[0][2])
            return details
        else:
            raise InvalidCategoryResponseFormat("The details response format is incorrect.")

    @staticmethod
    def _get_category_names_from_html(html) -> list[str]:
        """Extracts a list of extension category names from an HTML page"""
        return CATEGORY_NAMES_PATTERN.findall(html)

    @classmethod
    def quick_scan(cls) -> None:
        progress = ChromeProgressSaver()
        progress_info = progress.progress_info

        if not progress.is_finished:
            cls.scraped_categories = progress_info.get("scraped_categories")
            cls.resume_uncompleted_scan(progress_info)

        cls.start_new_scans()

        progress.save_completed_progress()

    @classmethod
    def scan_one_category(cls, category_name: str, last_token: str = ""):
        scraper = ChromeCategoryScraper(category_name, last_token)
        try:
            scraper.start()
            cls.scraped_categories.append(category_name)
        except (RequestException, RequestError) as e:
            cls.handle_scraping_error(category_name, scraper.get_token, e)

    @classmethod
    def resume_uncompleted_scan(cls, progress: Dict) -> None:
        now_category = progress.get("now_category")
        last_token = progress.get("token")

        cls.scan_one_category(now_category, last_token)

    @classmethod
    def start_new_scans(cls) -> None:
        all_categories = cls.get_categories()
        unscraped_categories = set(all_categories) - set(cls.scraped_categories)

        for unscraped_category in unscraped_categories:
            cls.scan_one_category(unscraped_category)

    def handle_scraping_error(self, category_name: str, break_token: str, error: Exception):
        progress = ChromeProgressSaver()
        progress.save_uncompleted_progress(self.scraped_categories,
                                           category_name, break_token)
        # TODO: 将break_reason使用Logger记录
        print(f"Error scraping category '{category_name}': {error}")
        # TODO: 这里直接使用exit退出是否有问题?
        sys.exit()
