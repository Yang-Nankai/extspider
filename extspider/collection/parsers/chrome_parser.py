# -*- coding: utf-8 -*-
import json
import re
from datetime import date, datetime
from codecs import BOM_UTF8
from typing import Callable, Optional
from extspider.collection.parsers.base_parser import DataMapper
from extspider.common.utils import is_valid_extension_id, is_valid_extension_version
from extspider.common.exception import UnexpectedDataStructure


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
            "identifier": self.valid_identifier,
            "version": self.valid_version,
            "manifest": self.parse_manifest,
            "byte_size": self.printable_bytes_to_int,
            "last_update": self.timestamp_to_date,
            "rating_average": self.valid_float,
            "user_count": self.valid_int,
            "rating_count": self.valid_int
        }

    @staticmethod
    def valid_identifier(identifier: str) -> str:
        if not is_valid_extension_id(str(identifier)):
            raise UnexpectedDataStructure("Cannot get the right identifier.")
        return identifier

    @staticmethod
    def valid_version(version: str) -> str:
        if not is_valid_extension_version(version):
            raise UnexpectedDataStructure("Cannot get the right version.")
        return version

    @staticmethod
    def valid_float(f_num: float) -> float:
        if f_num is None:
            return 0
        return round(float(f_num), 3)

    @staticmethod
    def valid_int(i_num: int) -> int:
        if i_num is None:
            return 0
        return int(i_num)

    @staticmethod
    def timestamp_to_date(timestamp: str) -> date:
        """Converts a Unix timestamp to a date object."""
        if timestamp is None:
            return None

        datetime_obj = datetime.utcfromtimestamp(int(timestamp))
        converted_date = datetime_obj.date()
        return converted_date

    @staticmethod
    def printable_bytes_to_int(printable_size: str) -> int:
        if printable_size is None:
            return None

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
        if json_string is None:
            return None

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
