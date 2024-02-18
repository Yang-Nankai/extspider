# -*- coding: utf-8 -*-

from typing import Iterable
from extspider.collection.details.base_extension_details import BaseExtensionDetails


class BaseCategoryScraper:

    def __init__(self, *args, **kwargs) -> None:
        self.category_name: str = None

    @property
    def BASE_URL(self):
        raise NotImplementedError("BASE_URL must be defined in a subclass")

    @classmethod
    def get_categories(cls) -> list[str]:
        raise NotImplementedError
