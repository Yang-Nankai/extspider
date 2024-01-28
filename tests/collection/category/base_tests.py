# -*- coding: utf-8 -*-

from unittest import TestCase

class BaseTests:
    class CategoryTestsCase(TestCase):

        @property
        def category_class(self):
            raise NotImplementedError


        def test_get_categories(self):
            categories: list[str] = self.category_class.get_categories()
            self.assertGreater(len(categories), 0)
            for category in categories:
                self.assertGreater(len(category), 0)