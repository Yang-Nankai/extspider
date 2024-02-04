# -*- coding: utf-8 -*-
import csv
import json
import re
from unittest import TestCase, skip

import requests

from extspider.collection.category.chrome_category_scraper import ChromeCategoryScraper
requests.packages.urllib3.disable_warnings()

class TestChromeCategoryScraper(TestCase):
    maxDiff = None

    @skip
    def test_update_body(self):
        categories = ChromeCategoryScraper.get_categories()
        test_category = categories[0]
        self.assertIsInstance(test_category, str)
        scraper = ChromeCategoryScraper(test_category)
        res_body = {'f.req': '[[["zTyKYc","[[null,[[3,\\"productivity/communication\\",null,null,2,[32,\\"\\"]]]]]",'
                             'null,"generic"]]]'}
        self.assertEqual(res_body, scraper.request_body)
        scraper.token = "abcdefg"
        res_body = {'f.req': '[[["zTyKYc","[[null,[[3,\\"productivity/communication\\",null,null,2,[32,'
                             '\\"abcdefg\\"]]]]]",null,"generic"]]]'}
        self.assertEqual(res_body, scraper.request_body)


    @skip
    def test_setup(self):
        scraper = ChromeCategoryScraper("productivity/communication")
        progress = scraper.setup()
        print(progress)

    def test_res_to_details_list(self):
        scraper = ChromeCategoryScraper("productivity/communication")
        HTTP_HEADERS = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                "AppleWebKit/537.36 (KHTML, like Gecko)"
                "Chrome/118.0.5993.90"
            ),
            "Host": "chromewebstore.google.com",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        }
        response = requests.post(scraper.target_url, headers=HTTP_HEADERS, data=scraper.request_body, verify=False)
        if response.status_code != 200:
            print("Exception")
        details = scraper._res_to_details_list(response.text)
        self.assertIsNotNone(details)
        self.assertIsInstance(details, list)

    @skip
    def test_start(self):
        scraper = ChromeCategoryScraper("productivity/communication")
        scraper.start()


    def test_request_details(self):
        scraper = ChromeCategoryScraper("productivity/communication")
        details = scraper.request_details()
        self.assertIsInstance(details, list)
        self.assertGreater(len(details), 0)


    def test_get_categories(self):
        categories = ChromeCategoryScraper.get_categories()
        self.assertGreater(len(categories), 0)
        for category_name in categories:
            self.assertIsInstance(category_name, str)
            self.assertGreater(len(category_name), 0)
