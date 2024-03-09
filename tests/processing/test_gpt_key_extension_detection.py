# -*- coding: utf-8 -*-
import re
import os
import json
from io import BytesIO
from unittest import TestCase
from extspider.processing.gpt_key_extension_detection import find_gpt_key_in_zip
from extspider.storage.database_handle import DatabaseHandle
from extspider.storage.models.extension import Extension
from extspider.storage.extension_handle import ExtensionHandle
from extspider.common.context import TEST_SAMPLES_PATH

GPT_KEY_EXTRACT_FILE = os.path.join(TEST_SAMPLES_PATH, "processing", "test_gpt_key_extract_result.json")


class TestGptKeyExtensionDetection(TestCase):
    def test_main(self):
        try:
            total_result = []
            download_path = ExtensionHandle.get_extension_storage_path(
                "lnoephicmnkhkjpmcaonmiapllfgolcm",
                "1.2"
            )

            result = find_gpt_key_in_zip(download_path)
            if result:
                info = {
                    "lnoephicmnkhkjpmcaonmiapllfgolcm": [
                        "1.2",
                        result
                    ]
                }
                total_result.append(info)

            with open(GPT_KEY_EXTRACT_FILE, "w") as file:
                json.dump(total_result, file, ensure_ascii=False,
                          indent=4)  # Proper JSON dumping with improved readability
        except Exception as e:
            # Consider logging the exception details to a file or logging service
            print(f"An error occurred: {e}")
        self.assertTrue(os.path.exists(GPT_KEY_EXTRACT_FILE))
