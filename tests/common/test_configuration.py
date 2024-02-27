# -*- coding: utf-8 -*-
import logging
from unittest import TestCase, skipUnless
from extspider.common import configuration as conf


class TestConfiguration(TestCase):
    """
    TestConfiguration ensures correct configuration of global variables
    """
    def test_prod_version(self):
        """Ensures that the chrome binary path is correct"""
        prod_version = conf.PROD_VERSION
        self.assertIsNotNone(prod_version)
        self.assertEqual(type(prod_version), str)
        self.assertGreater(len(prod_version), 0)

    def test_request_id(self):
        """Ensures that the request id (chrome_category & chrome_detail) is correct"""
        chrome_category_request_id = conf.CHROME_CATEGORY_REQUEST_ID
        self.assertIsNotNone(chrome_category_request_id)
        self.assertEqual(type(chrome_category_request_id), str)
        self.assertGreater(len(chrome_category_request_id), 0)
        chrome_detail_request_id = conf.CHROME_DETAIL_REQUEST_ID
        self.assertIsNotNone(chrome_detail_request_id)
        self.assertEqual(type(chrome_detail_request_id), str)
        self.assertGreater(len(chrome_detail_request_id), 0)

    def test_proxies(self):
        """Ensure that the PROXIES is correct"""
        proxies = conf.PROXIES
        self.assertIsNotNone(proxies)
        self.assertIsNotNone(proxies["http"])

    @skipUnless(conf.IS_FEISHU_ENABLED,
                "Testing feishu-related parameters")
    def test_feishu_logging(self):
        """Ensures that the feishu parameters were set correctly"""
        webhook_url = conf.FEISHU_WEBHOOK_URL

        self.assertIsNotNone(webhook_url)
        self.assertEqual(type(webhook_url), str)
        self.assertGreater(len(webhook_url), 0)
