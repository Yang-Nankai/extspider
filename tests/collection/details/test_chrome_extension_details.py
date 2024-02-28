# -*- coding: utf-8 -*-
from pathlib import Path
from tests.collection.details.base_tests import BaseTests as BT
from extspider.collection.details.chrome_extension_details import ChromeExtensionDetails
from extspider.common.context import TEST_SAMPLES_PATH
from extspider.common.exception import MaxRequestRetryError,UnexpectedDataStructure

SAMPLES_ROOT = Path(TEST_SAMPLES_PATH) / "chrome_extension_details"
TEST_DOWNLOAD_PATH = SAMPLES_ROOT / "test_extension.crx"
TEST_MANIFEST_PATH = SAMPLES_ROOT / "manifest.json"
TEST_BAD_DOWNLOAD_PATH = SAMPLES_ROOT / "test_bad_extension.crx"


class TestChromeExtensionDetails(BT.DetailsTestCase):

    @property
    def details_class(self):
        return ChromeExtensionDetails

    def setUp(self):
        self.extension = ChromeExtensionDetails("ejonaglbdpcfkgbcnidjlnjogfdgbofp")
        self.bad_extension = ChromeExtensionDetails("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

    def test_get_extension_detail(self):
        # Extension exists
        processed_data = self.extension.get_extension_detail()
        self.assertIsNotNone(processed_data)
        self.assertEqual(len(processed_data), 12)
        self.assertIsNotNone(processed_data[0])

        # Extension not exists
        with self.assertRaises(UnexpectedDataStructure) as e:
            processed_data = self.bad_extension.get_extension_detail()
            self.assertEqual(len(processed_data), 12)
            for data in processed_data:
                self.assertIsNone(data)

        # TODO: 这里需要当连接不到谷歌服务器的时候响应，需要增加测试！！！
        # if internet_not_connected:
        # cannot request
        # processed_data = self.bad_extension.get_extension_detail()

    def test_update_details(self):
        has_changed = self.extension.update_details()
        self.assertTrue(has_changed)
        has_changed = self.extension.update_details()
        self.assertFalse(has_changed)

    def test_download(self):
        # Extension exists
        self.extension.download(str(TEST_DOWNLOAD_PATH))
        crx_file_exists = TEST_DOWNLOAD_PATH.exists()
        self.assertTrue(crx_file_exists)
        manifest_file_exists = TEST_MANIFEST_PATH.exists()
        self.assertTrue(manifest_file_exists)

        # Extentison not exists
        with self.assertRaises(MaxRequestRetryError):
            self.bad_extension.download(str(TEST_BAD_DOWNLOAD_PATH))
            crx_file_exists = TEST_BAD_DOWNLOAD_PATH.exists()
            self.assertTrue(crx_file_exists)

    def tearDown(self) -> None:
        if TEST_DOWNLOAD_PATH.exists():
            TEST_DOWNLOAD_PATH.unlink()
        if TEST_MANIFEST_PATH.exists():
            TEST_MANIFEST_PATH.unlink()
        if TEST_BAD_DOWNLOAD_PATH.exists():
            TEST_MANIFEST_PATH.unlink()
