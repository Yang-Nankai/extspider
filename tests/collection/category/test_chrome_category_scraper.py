# -*- coding: utf-8 -*-
import csv
from unittest import TestCase, skip
from extspider.collection.category.chrome_category_scraper import ChromeCategoryScraper


class TestChromeCategoryScraper(TestCase):

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
    def test_start(self):
        categories = ChromeCategoryScraper.get_categories()
        test_category = categories[0]
        self.assertIsInstance(test_category, str)
        scraper = ChromeCategoryScraper(test_category)
        scraper.start()


    @skip
    def test_request_details(self):
        categories = ChromeCategoryScraper.get_categories()
        test_category = categories[0]
        self.assertIsInstance(test_category, str)
        scraper = ChromeCategoryScraper(test_category)
        details = scraper.request_details()
        self.assertIsInstance(details, list)
        self.assertGreater(len(details), 0)


    @skip
    def test_get_categories(self):
        categories = ChromeCategoryScraper.get_categories()
        self.assertGreater(len(categories), 0)
        for category_name in categories:
            self.assertIsInstance(category_name, str)
            self.assertGreater(len(category_name), 0)
