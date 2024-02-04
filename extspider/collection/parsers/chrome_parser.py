# -*- coding: utf-8 -*-
import json
import re
from codecs import BOM_UTF8
from typing import Callable

from extspider.collection.parsers.base_parser import DataMapper


class PartialDetailsMapper(DataMapper):
    """Maps elements in a list containing some data about an extension."""

    INDEX_MAP = {
        "identifier": 0,
        "name": 2,
        "rating_average": 3,
        "rating_count": 4,
        "user_estimate": 14
    }

    @classmethod
    def map_extension_items(cls, extension_items: list) -> list:
        """Performs mapping on all the extension data in the given list."""
        return [
            cls.map_data_list(item)
            for item in extension_items
        ]


class ChromeCategoryResponseMapper(DataMapper):
    """Maps category responses from the Chrome Web Store."""
    INDEX_MAP = {
        "details_data": [0, 0, 0, 13, 0, 0],
        "token": [2, 0]
    }


class ChromeExtensionResponseMapper(DataMapper):
    """Maps Extension detail responses from the Chrome Web Store"""
    INDEX_MAP = {
        "identifier": [0, 0],
        "name": [0, 2],
        "version": [13],
        "last_update": [14, 0], # timestamp
        "description": [0, 6],
        "category": [0, 11, 0],
        "rating_average": [0, 3], # between 1 - 5
        "rating_count": [0, 4],
        "user_count": [0, 14],
        "manifest": [20], # encoded
        "byte_size": [15], # printable format (e.g. '236KiB')
        "developer_name": [10, 5],
        "recommended_extensions": [22], # list with different structure
    }

    @property
    def DATA_TRANSFORMERS(self) -> dict[str, Callable]:
        return {
            "manifest": self.parse_manifest,
            "byte_size": self.printable_bytes_to_float,
            "recommended_extensions": PartialDetailsMapper.map_extension_items
        }

    @staticmethod
    def printable_bytes_to_float(printable_size) -> int:
        unit_conversion = {
            "KiB": 1024,
            "MiB": 1024 ** 2,
            "GiB": 1024 ** 3
        }
        number, unit = printable_size[:-3], printable_size[-3:]
        return float(number) * unit_conversion[unit]

    @staticmethod
    def parse_manifest(json_string: str) -> str:
        """
        Parses a JSON-formatted string, accounting for non-standard sections
        such as commented sequences, unescaped control characters,
        Byte Order Mark (BOM), etc.
        """
        # Remove commented sequences
        json_string = re.sub(r'\n\s*//.*', '', json_string, flags=re.MULTILINE)
        json_string = re.sub(r'/\*.*?\*/', '', json_string, re.DOTALL)
        # Remove Byte Order Mark
        bom = BOM_UTF8.decode("utf-8")
        if json_string.startswith(bom):
            json_string = json_string[len(bom):]
        # Remove control characters (tab, newline, carriage return)
        json_string = re.sub(r'\t', '', json_string)
        json_string = re.sub(r'\n', '', json_string)
        json_string = re.sub(r'\r', '', json_string)
        json_string = json_string.strip()
        return json.loads(json_string)

