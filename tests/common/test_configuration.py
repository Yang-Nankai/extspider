# -*- coding: utf-8 -*-
import logging
import os
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

    def test_http_headers(self):
        """Ensure that the HTTP_HEADERS is correct"""
        http_headers = conf.HTTP_HEADERS
        self.assertIsInstance(http_headers, dict)
        self.assertIsNotNone(http_headers)
        self.assertIsNotNone(http_headers.get("User-Agent"))



    # @skipUnless(conf.IS_TELEGRAM_ENABLED,
    #             "Testing Telegram-related parameters")
    # def test_telegram_logging(self):
    #     """Ensures that the telegram parameters were set correctly"""
    #     token = conf.TELEGRAM_TOKEN
    #     user_id = conf.TELEGRAM_USER_ID
    #
    #     self.assertIsNotNone(token)
    #     self.assertEqual(type(token), str)
    #     self.assertGreater(len(token), 0)
    #
    #     self.assertIsNotNone(user_id)
    #     self.assertEqual(type(user_id), int)
    #     self.assertNotEqual(user_id, 0)
    #
    #     logger = logging.getLogger("test_configuration")
    #     logger.setLevel(logging.INFO)
    #     tg_logger.setup(logger, token=token, users=[user_id])
    #     logger.info("Testing logging functionality")
