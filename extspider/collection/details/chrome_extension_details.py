# -*- coding: utf-8 -*-
import csv
import datetime
import io
import json
import os
import re
import requests
import struct
import shutil
from pathlib import Path
from zipfile import ZipFile, BadZipFile
from typing import Dict, List, Iterable, Optional
from io import BufferedReader, BytesIO
from extspider.collection.details.base_extension_details import BaseExtensionDetails
from extspider.common.exception import MaxRequestRetryError
from extspider.collection.parsers.chrome_parser import ChromeExtensionDetailsMapper
from extspider.common.configuration import PROD_VERSION
from extspider.storage.database_handle import DatabaseHandle
from extspider.common.utils import request_retry_with_backoff, details_response_to_json_format
from extspider.common.configuration import (CHROME_DETAIL_REQUEST_ID,
                                            PROXIES, HTTP_HEADERS)
from extspider.common.context import DATA_PATH

requests.packages.urllib3.disable_warnings()

DETAILS_PATTERN = re.compile(r'(\[\[.*\]\])')
BASE_URL = "https://chromewebstore.google.com"
BASE_REQUEST_URL = BASE_URL + "/_/ChromeWebStoreConsumerFeUi/data/batchexecute"


class BadCrx(IOError):
    pass


class ChromeExtensionDetails(BaseExtensionDetails):

    @property
    def request_body(self) -> Dict:
        return {
            "f.req": f'[[["{CHROME_DETAIL_REQUEST_ID}",'
                     f'"[\\"{self.identifier}\\"]",null,"1"]]]'
        }

    @property
    def download_url(self) -> str:
        return ("https://clients2.google.com/service/update2/crx"
                "?response=redirect"
                f"&prodversion={PROD_VERSION}"
                "&acceptformat=crx3,puff"
                f"&x=id%3D{self.identifier}%26uc")

    @property
    def details_url(self) -> str:
        return BASE_REQUEST_URL

    @request_retry_with_backoff(max_retries=5, retry_interval=2)
    def download(self, download_path: str) -> bool:
        """Downloads the extension crx file and extract the manifest.json
        to specific path.

        Args:
            download_path (str): The path where the CRX file will be downloaded.

        Returns:
            True if the download is successful, False otherwise
        """
        if Path(download_path).exists():
            return True

        directory_path = Path(download_path).parent
        Path(directory_path).mkdir(parents=True, exist_ok=True)

        try:
            response = requests.get(self.download_url, timeout=120,
                                    stream=True, proxies=PROXIES)
            response.raise_for_status()
            with open(download_path, "wb") as extension_file:
                shutil.copyfileobj(response.raw, extension_file)
                # TODO: load_manifest，这里是不是不应该出现，代码是否复杂，需要review
                self.load_manifest(download_path)
        except MaxRequestRetryError as e:
            # TODO: 这里需要日志记录
            print(f"Failed to download {self.identifier}: {str(e)}")

        return Path(download_path).exists()

    @request_retry_with_backoff(max_retries=5, retry_interval=2)
    def get_extension_detail(self) -> Optional[List[str]]:
        try:
            response = requests.post(self.details_url,
                                     headers=HTTP_HEADERS,
                                     data=self.request_body,
                                     proxies=PROXIES)
            response.raise_for_status()
            details_data = details_response_to_json_format(response.text)
            processed_data = ChromeExtensionDetailsMapper.map_data_list(details_data)
            return processed_data
        except MaxRequestRetryError as e:
            print(f"Failed to get {self.identifier} detail: {str(e)}")
            return

    def update_details(self) -> bool:
        """Scrapes the extension's online details

        Returns:
            True if the detail were updated, False otherwise
        """
        old_hash = hash(self)
        process_data = self.get_extension_detail()
        if process_data is not None:
            self.update_from(process_data)
        new_hash = hash(self)
        return old_hash != new_hash

    def load_manifest(self, crx_path: str):
        crx_path_obj = Path(crx_path)
        manifest_path = crx_path_obj.parent / "manifest.json"
        if not manifest_path.is_file():
            self.extract_manifest(crx_path)

    def extract_manifest(self, crx_path: str) -> str:
        crx_path_obj = Path(crx_path)
        zip_file = self.get_zip_archive(crx_path)

        if zip_file is not None:
            zip_file.extract("manifest.json", crx_path_obj.parent)
            del zip_file

    def get_zip_archive(self, crx_path: str) -> Optional[ZipFile]:
        with open(crx_path, "rb") as crx_file:
            try:
                self.strip_crx_headers(crx_file)
                zip_file = ZipFile(
                    BytesIO(crx_file.read())
                )
            except BadZipFile:
                return None

        return zip_file

    @classmethod
    def strip_crx_headers(cls, crx_file: BufferedReader) -> None:
        magic_number_bytes = crx_file.read(4)
        version_bytes = crx_file.read(4)

        cls.assert_magic_number(magic_number_bytes)
        if cls.get_crx_version(version_bytes) <= 2:
            cls.strip_crx2(crx_file)
        else:
            cls.strip_crx3(crx_file)

    @staticmethod
    def assert_magic_number(crx_bytes: bytes) -> None:
        magic_number = crx_bytes.decode("utf-8")
        if magic_number != "Cr24":
            raise BadCrx(f"'Unexpected magic number: {magic_number}.")

    @staticmethod
    def get_crx_version(crx_bytes: bytes) -> int:
        # extract an integer from bytes following little-endian order
        return struct.unpack("<I", crx_bytes)[0]

    @staticmethod
    def strip_crx2(crx_file: BufferedReader) -> None:
        public_key_length_bytes = crx_file.read(4)
        signature_length_bytes = crx_file.read(4)

        public_key_length = struct.unpack("<I", public_key_length_bytes)[0]
        signature_length = struct.unpack("<I", signature_length_bytes)[0]

        crx_file.seek(public_key_length, signature_length, os.SEEK_CUR)

    @staticmethod
    def strip_crx3(crx_file: BufferedReader) -> None:
        header_length_bytes = crx_file.read(4)
        header_length = struct.unpack("<I", header_length_bytes)[0]

        crx_file.seek(header_length, os.SEEK_CUR)

    # TODO: 这里需不需要还是怎么更改位置
    def save_metadata(self):
        # TODO: 对于version这里需要更改逻辑，如果没有则调用version_name
        extension = DatabaseHandle.store_extension(
            self.identifier, self.name, self.developer_name, self.category,
            self.user_count, self.rating_count, self.rating_average,
            self.manifest, self.byte_size, self.version, self.last_update
        )
        #TODO: 存储permission，这里还是有点奇怪，不如直接将extension和version的数据绑定起来
        # 但是需要考虑的是还需要有当日CWS中存在的extension的存储，这里还是需要根据最后的结果来判断
        DatabaseHandle.store_extension_permission(extension)
