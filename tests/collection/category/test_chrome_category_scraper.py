# -*- coding: utf-8 -*-
import requests
from unittest import TestCase, skip
from extspider.collection.category.chrome_category_scraper import ChromeCategoryScraper
from extspider.common.exception import MaxRequestRetryError
requests.packages.urllib3.disable_warnings()


class TestChromeCategoryScraper(TestCase):

    def setUp(self):
        self.scraper = ChromeCategoryScraper("productivity/communication")

    def test_request_simple_details(self):
        details = self.scraper.request_simple_details()
        self.assertIsNotNone(details)
        self.assertGreater(len(details), 0)

        # Given the token
        self.scraper.token = "QWJ0WnBNWm93QkIwdXl0amJkNEsxYjFzN1ZOUnJVWmhWT3VUVFRKUEFzQ1B" \
                             "kLTNiSEJEemhJNDlHbGFoNzREUmlwd1BpaFM1RXk1U3JQNVpYVFkxZ1JPVEdtSW" \
                             "41Y0lEZlpWLVJmMGVPU1NEMXR2OGpZclpXbVI3VHlXQXZRY0ZtVEJKb1VTMDNudTY1" \
                             "MHFjdVpEUXpzUDE4X1RYX2xmb2MwX0xka1p5cnNfSE1TRTBnb3Z5eXNmbVVlVWttd3" \
                             "pkNkwtTjZYeDM1RVdtbkpRVlB3VzVhcWN1dnZvT3ZwLVpOcUdzN0Myd2ZsQzZYbFN" \
                             "SQXFpSHNBZ0pTZ0xEdWUzbW5ONWx3eWdadXZlOXJnPT0="
        token_details = self.scraper.request_simple_details()
        self.assertIsNotNone(token_details)
        self.assertGreater(len(token_details), 0)

        self.assertNotEqual(details, token_details)

        # Not exists category
        self.bad_scraper = ChromeCategoryScraper("productivity/fun")
        with self.assertRaises(MaxRequestRetryError):
            bad_details = self.bad_scraper.request_simple_details()
            self.assertIsNone(bad_details)
        self.bad_scraper.ids_writter.close()

    def test_collect_and_store(self):
        details_data = self.scraper.request_simple_details()
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
