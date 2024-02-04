# -*- coding: utf-8 -*-
import io
import json
import os
import pathlib
import re
import shutil
from dataclasses import fields
from typing import Dict, List, Iterable

import requests

from extspider.collection.details.base_extension_details import BaseExtensionDetails
from extspider.common.exception import ExtensionRequestError
from extspider.collection.parsers.chrome_parser import ChromeExtensionResponseMapper

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


class ChromeExtensionDetails(BaseExtensionDetails):

    @staticmethod
    def _res_to_details_list(response: str):
        if response:
            details = re.findall(DETAILS_PATTERN, response)[0]
            return json.loads(json.loads(details)[0][2])
            # TODO: Need review
        else:
            pass

    @property
    def request_body(self) -> Dict:
        # TODO: Need refactor
        self.request_id = "xY2Ddd"
        return {
            "f.req": f'[[["{self.request_id}","[\\"{self.identifier}\\"]",null,"1"]]]'
        }

    @property
    def download_url(self) -> str:
        # TODO: Make `prodversion` easier to update (configuration)
        return ("https://clients2.google.com/service/update2/crx"
                "?response=redirect"
                "&prodversion=118.0.5993.90"
                "&acceptformat=crx3,puff"
                f"&x=id%3D{self.identifier}%26uc")

    @property
    def details_url(self) -> str:
        return BASE_REQUEST_URL

    def download(self, download_path: str) -> bool:
        """Downloads the extension CRX archive to specific path.

        Returns:
            True if the download is successful, False otherwise
        """
        directory_path = os.path.dirname(download_path)
        pathlib.Path(directory_path).mkdir(parents=True, exist_ok=True)
        # TODO: Exception
        response = requests.get(self.download_url, timeout=120, stream=True)
        response.raise_for_status()

        with open(download_path, "wb") as extension_file:
            content_stream = io.BytesIO(response.content)
            shutil.copyfileobj(content_stream, extension_file)
        return os.path.exists(download_path)


    def get_extension_detail(self) -> List:
        response = requests.post(self.details_url, headers=HTTP_HEADERS, data=self.request_body, verify=False)
        if response.status_code != 200:
            raise ExtensionRequestError
        raw_data = self._res_to_details_list(response.text)
        processed_data = ChromeExtensionResponseMapper.map_data_list(raw_data)
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


