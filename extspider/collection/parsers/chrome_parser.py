# -*- coding: utf-8 -*-
import json
import re
from datetime import date, datetime
from codecs import BOM_UTF8
from typing import Callable
from extspider.collection.parsers.base_parser import DataMapper


class ChromeCategoryResponseMapper(DataMapper):
    """Maps category responses from the Chrome Web Store."""
    INDEX_MAP = {
        "details_data": [0, 0, 0, 13, 0, 0],
        "token": [2, 0]
    }


class ChromeExtensionDetailsMapper(DataMapper):
    """Maps Extension detail responses from the Chrome Web Store"""
    INDEX_MAP = {
        "identifier": [0, 0],
        "name": [0, 2],
        "version": [13],
        "last_update": [14, 0],  # timestamp
        "description": [0, 6],
        "category": [0, 11, 0],
        "rating_average": [0, 3],  # between 1 - 5
        "rating_count": [0, 4],
        "user_count": [0, 14],
        "manifest": [20],  # encoded
        "byte_size": [15],  # printable format (e.g. '236KiB')
        "developer_name": [10, 5]
    }

    @property
    def DATA_TRANSFORMERS(self) -> dict[str, Callable]:
        return {
            "manifest": self.parse_manifest,
            "byte_size": self.printable_bytes_to_int,
            "last_update": self.timestamp_to_date,
            #TODO: 这里严重需要改变
            "user_count": self.str_to_int,
            "rating_count": self.str_to_int,
            "rating_average": self.str_to_float
        }

    @staticmethod
    def str_to_int(count) -> int:
        """Converts a user count to int, if none return 0."""
        if count is None:
            return 0
        return int(count)

    @staticmethod
    def str_to_float(rating) -> float:
        if rating is None:
            return 0
        return round(float(rating), 2)

    @staticmethod
    def timestamp_to_date(timestamp) -> date:
        """Converts a Unix timestamp to a date object."""
        datetime_obj = datetime.utcfromtimestamp(int(timestamp))
        converted_date = datetime_obj.date()
        return converted_date

    @staticmethod
    def printable_bytes_to_int(printable_size) -> int:
        unit_conversion = {
            "KiB": 1024,
            "MiB": 1024 ** 2,
            "GiB": 1024 ** 3
        }
        number, unit = printable_size[:-3], printable_size[-3:]
        return int(float(number) * unit_conversion[unit])

    @staticmethod
    def parse_manifest(json_string: str) -> str:
        """
        Parses a JSON-formatted string, accounting for non-standard sections
        such as commented sequences, unescaped control characters,
        Byte Order Mark (BOM), etc.
        """
        # Remove commented sequences
        json_string = re.sub(r'\n\s*//.*', '', json_string, flags=re.MULTILINE)
        # TODO: 对于这里JSON格式需要进一步的查看，这里存在bug
        # json_string = re.sub(r'/\*.*?\*/', '', json_string, re.DOTALL)
        # Remove Byte Order Mark
        bom = BOM_UTF8.decode("utf-8")
        if json_string.startswith(bom):
            json_string = json_string[len(bom):]
        # Remove control characters (tab, newline, carriage return)
        json_string = re.sub(r'\t', '', json_string)
        json_string = re.sub(r'\n', '', json_string)
        json_string = re.sub(r'\r', '', json_string)
        json_string = json_string.strip()
        # print(json_string)
        return json.loads(json_string)

