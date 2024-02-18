# -*- coding: utf-8 -*-
import io
import json
import os
import pathlib
import re
import requests
import struct
import shutil
from zipfile import ZipFile, BadZipFile
from typing import Dict, List, Iterable, Optional
from io import BufferedReader, BytesIO
from extspider.collection.details.base_extension_details import BaseExtensionDetails
from extspider.common.exception import (ExtensionRequestDetailError, InvalidCategoryResponse,
                                        ExtensionDownloadExtensionError)
from extspider.collection.parsers.chrome_parser import ChromeExtensionDetailsMapper
from extspider.common.configuration import PROD_VERSION
from extspider.storage.database_handle import DatabaseHandle
from extspider.common.utils import request_retry_with_backoff

requests.packages.urllib3.disable_warnings()

DETAILS_PATTERN = re.compile(r'(\[\[.*\]\])')
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        "AppleWebKit/537.36 (KHTML, like Gecko)"
        "Chrome/118.0.5993.90"
    ),
    "Host": "chromewebstore.google.com",
    "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
}
BASE_URL = "https://chromewebstore.google.com"
BASE_REQUEST_URL = BASE_URL + "/_/ChromeWebStoreConsumerFeUi/data/batchexecute"


class BadCrx(IOError):
    pass


class ChromeExtensionDetails(BaseExtensionDetails):

    @staticmethod
    def _response_to_details_list(response: str) -> List:
        details_match = re.findall(DETAILS_PATTERN, response)

        if details_match:
            details = json.loads(json.loads(details_match[0])[0][2])
            return details
        else:
            raise InvalidCategoryResponse

    @property
    def request_body(self) -> Dict:
        # TODO: Here need to be considered again
        request_id = "xY2Ddd"
        return {
            "f.req": f'[[["{request_id}","[\\"{self.identifier}\\"]",null,"1"]]]'
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
        """Downloads the extension CRX archive to specific path.

        Returns:
            True if the download is successful, False otherwise
        """
        if pathlib.Path(download_path).exists():
            # TODO: 这里是否需要，这样就会当作一个benchmark对待了，则每次不需要那么久
            return True
        directory_path = os.path.dirname(download_path)
        pathlib.Path(directory_path).mkdir(parents=True, exist_ok=True)
        # TODO: Exception RequestException需要
        response = requests.get(self.download_url, timeout=120, stream=True)
        if response.status_code != 200:
            raise ExtensionDownloadExtensionError

        with open(download_path, "wb") as extension_file:
            content_stream = io.BytesIO(response.content)
            shutil.copyfileobj(content_stream, extension_file)

        # TODO: load_manifest
        self.load_manifest(download_path)
        return os.path.exists(download_path)

    def get_extension_detail(self) -> List:
        response = requests.post(self.details_url, headers=HTTP_HEADERS, data=self.request_body)
        if response.status_code != 200:
            raise ExtensionRequestDetailError
        details_data = self._response_to_details_list(response.text)
        processed_data = ChromeExtensionDetailsMapper.map_data_list(details_data)
        return processed_data

    def update_details(self) -> bool:
        """Scrapes the extension's online details

        Returns:
            True if the detail were updated, False otherwise
        """
        old_hash = hash(self)
        process_data = self.get_extension_detail()
        self.update_from(process_data)
        new_hash = hash(self)
        return old_hash != new_hash

    # TODO: 这里需不需要还是怎么更改位置
    def save_metadata(self) -> None:
        DatabaseHandle.store_extension(self.identifier,
                                       self.name,
                                       self.developer_name,
                                       self.category,
                                       self.user_count,
                                       self.rating_count,
                                       self.rating_average,
                                       self.manifest,
                                       self.byte_size,
                                       self.version,
                                       self.last_update)

    def load_manifest(self, crx_path: str) -> None:
        manifest_path = os.path.join(os.path.dirname(crx_path), "manifest.json")
        if not os.path.isfile(manifest_path):
            self.extract_manifest(crx_path)

    def extract_manifest(self, crx_path: str) -> str:
        zip_file = self.get_zip_archive(crx_path)
        if zip_file is not None:
            zip_file.extract("manifest.json", os.path.dirname(crx_path))
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
