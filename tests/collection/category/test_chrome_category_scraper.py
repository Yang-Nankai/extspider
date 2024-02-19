# -*- coding: utf-8 -*-
import requests
from unittest import TestCase, skip
from extspider.collection.category.chrome_category_scraper import ChromeCategoryScraper

requests.packages.urllib3.disable_warnings()

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        "AppleWebKit/537.36 (KHTML, like Gecko)"
        "Chrome/118.0.5993.90"
    ),
    "Host": "chromewebstore.google.com",
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
}


class TestChromeCategoryScraper(TestCase):

    def setUp(self):
        self.scraper = ChromeCategoryScraper("productivity/communication")

    def test_request_details(self):
        details = self.scraper.request_details()
        self.assertIsNotNone(details)
        self.assertGreater(len(details), 0)

        # Given the token
        self.scraper.token = "QWJ0WnBNWm93QkIwdXl0amJkNEsxYjFzN1ZOUnJVWmhWT3VUVFRKUEFzQ1B" \
                             "kLTNiSEJEemhJNDlHbGFoNzREUmlwd1BpaFM1RXk1U3JQNVpYVFkxZ1JPVEdtSW" \
                             "41Y0lEZlpWLVJmMGVPU1NEMXR2OGpZclpXbVI3VHlXQXZRY0ZtVEJKb1VTMDNudTY1" \
                             "MHFjdVpEUXpzUDE4X1RYX2xmb2MwX0xka1p5cnNfSE1TRTBnb3Z5eXNmbVVlVWttd3" \
                             "pkNkwtTjZYeDM1RVdtbkpRVlB3VzVhcWN1dnZvT3ZwLVpOcUdzN0Myd2ZsQzZYbFN" \
                             "SQXFpSHNBZ0pTZ0xEdWUzbW5ONWx3eWdadXZlOXJnPT0="
        token_details = self.scraper.request_details()
        self.assertIsNotNone(token_details)
        self.assertGreater(len(token_details), 0)

        self.assertNotEqual(details, token_details)

        # Not exists category
        self.bad_scraper = ChromeCategoryScraper("productivity/fun")
        bad_details = self.bad_scraper.request_details()
        self.assertIsNone(bad_details)
        self.bad_scraper.ids_writter.close()

    def test_collect_and_store(self):
        details_data = self.scraper.request_details()
        self.assertGreater(len(details_data), 0)
        self.scraper.collect_and_store(details_data)
        self.assertGreater(len(self.scraper.found_ids), 0)

    def test_get_categories(self):
        categories = ChromeCategoryScraper.get_categories()
        self.assertGreater(len(categories), 0)
        for category_name in categories:
            self.assertIsInstance(category_name, str)
            self.assertGreater(len(category_name), 0)

    @skip
    def test_quick_scan(self):
        ChromeCategoryScraper.quick_scan()

    def tearDown(self) -> None:
        # close the resource
        self.scraper.ids_writter.close()
