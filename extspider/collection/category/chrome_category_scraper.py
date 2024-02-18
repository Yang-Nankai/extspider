# -*- coding: utf-8 -*-
import csv
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
from extspider.collection.details.chrome_extension_details import ChromeExtensionDetails
from typing import Dict, List

requests.packages.urllib3.disable_warnings()

CATEGORY_NAMES_PATTERN = re.compile(r',\\\"([a-z_]+/[a-z_]+)\\\"')
DETAILS_PATTERN = re.compile(r'(\[\[.*\]\])')

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        "AppleWebKit/537.36 (KHTML, like Gecko)"
        "Chrome/118.0.5993.90"
    ),
    "Host": "chromewebstore.google.com",
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
}
BASE_URL = "https://chromewebstore.google.com"
BASE_SOURCE_PATH = "category/extensions/{category}"
BASE_REQUEST_URL = BASE_URL + "/_/ChromeWebStoreConsumerFeUi/data/batchexecute"


class ChromeCategoryScraper(BaseCategoryScraper):
    # TODO: Support proxy
    # results = list()
    found_ids = set()
    scraped_categories = list()

    def __init__(self, category_name: str, token: str = "") -> None:
        self.category_name = category_name
        self.source_path = BASE_SOURCE_PATH.format(category=category_name)
        self.once_num = 64  # Num of once request extensions
        self.token = token
        # TODO: Get request_id from html page automatically
        self.request_id = "zTyKYc"
        self.target_url = f"{BASE_REQUEST_URL}?rpcids={self.request_id}&source-path={self.source_path}"
        # self.backup_writter = csv.writer(
        #     open(f"{DATA_PATH}/categories_results.csv", "a", newline='', encoding='utf-8')
        # )
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
        print(f'Starting collect category: {self.category_name} ...')
        index = 0

        while True:
            index += 1
            print(f"Cycle: {index}")

            # TODO: need change the name
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
        response = requests.post(self.target_url, headers=HTTP_HEADERS, data=self.request_body)
        if response.status_code != 200:
            raise CategoryRequestError
        details_data = self._response_to_details_list(response.text)
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
    def _response_to_details_list(response: str) -> List:
        details_match = re.findall(DETAILS_PATTERN, response)

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
        # TODO: 删除Progress功能，感觉没什么用
        progress_info = ChromeProgressSaver()
        progress = progress_info.load_progress()

        if progress:
            status = progress.get("status")
            cls.scraped_categories = progress.get("scraped_categories")

            if status == 0:  # uncompleted
                cls.resume_uncompleted_scan(progress)

        categories = cls.get_categories()
        cls.start_new_scans(categories)

        progress_info.save_progress(1)

    @classmethod
    def resume_uncompleted_scan(cls, progress: Dict) -> None:
        now_category = progress.get("now_category")
        break_reason = progress.get("break_reason")

        print("Last break reason: ", break_reason)

        scraper = ChromeCategoryScraper(now_category, progress.get("token"))
        try:
            scraper.start()
            cls.scraped_categories.append(now_category)
        except Exception as e:
            cls.handle_scraping_error(now_category, scraper.get_token, e)

    @classmethod
    def start_new_scans(cls, categories: List[str]) -> None:
        for category_name in categories:
            if category_name not in cls.scraped_categories:
                scraper = ChromeCategoryScraper(category_name)
                try:
                    scraper.start()
                    cls.scraped_categories.append(category_name)
                except Exception as e:
                    cls.handle_scraping_error(category_name, scraper.get_token, e)

    @classmethod
    def handle_scraping_error(cls, category_name: str, break_token: str, error: Exception) -> None:
        # Handle or log the scraping error as needed
        print(f"Error scraping category '{category_name}': {error}")
        progress_info = ChromeProgressSaver()
        progress_info.save_progress(0, cls.scraped_categories, category_name, break_token, str(error))
        sys.exit()
