# -*- coding: utf-8 -*-


from extspider.collection.parsers.base_parser import DataMapper


class CategoryResponseMapper(DataMapper):
    """Maps responses from the Chrome Web Store."""
    INDEX_MAP = {
        "details_data": [0, 0, 0, 13, 0, 0],
        "token": [2, 0]
    }




