# -*- coding: utf-8 -*-
from tests.collection.category.base_tests import BaseTests as BT
from extspider.collection.category.base_category_scraper import BaseCategoryScraper

class TestBaseCategoryScraper(BT.CategoryTestsCase):

    @property
    def details_class(self):
        return BaseCategoryScraper

    def test_get_categories(self):
        with self.assertRaises(NotImplementedError):
            BaseCategoryScraper.get_categories()