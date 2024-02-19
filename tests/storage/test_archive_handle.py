import shutil
import os
from zipfile import ZipFile
from unittest import TestCase
from extspider.storage.archive_handle import (ArchiveHandle,
                                              EXTENSIONS_DIRECTORY_PATH)
from extspider.storage.database_handle import DatabaseHandle
from extspider.common.context import TEST_SAMPLES_PATH

ARCHIVE_HANDLE_SAMPLES = os.path.join(TEST_SAMPLES_PATH, "archive_handle")
ARCHIVE_CRX_PATH = os.path.join(ARCHIVE_HANDLE_SAMPLES, "sample_extension.crx")
ARCHIVE_ZIP_PATH = os.path.join(ARCHIVE_HANDLE_SAMPLES, "sample_extension.zip")
ARCHIVE_EXTRACTED_PATH = os.path.join(ARCHIVE_HANDLE_SAMPLES,
                                      "sample_extension")


class TestArchiveHandle(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        with ZipFile(ARCHIVE_ZIP_PATH, "r") as zip_reference:
            zip_reference.extractall(ARCHIVE_EXTRACTED_PATH)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(ARCHIVE_EXTRACTED_PATH)

    def setUp(self) -> None:
        self.rename_actual_directory_path()
        if not os.path.isfile(self.temporary_sample_extension_path):
            shutil.move(self.sample_extension_path,
                        f"{self.sample_extension_path}.backup")

    def tearDown(self) -> None:
        if os.path.exists(EXTENSIONS_DIRECTORY_PATH):
            if os.path.islink(EXTENSIONS_DIRECTORY_PATH):
                os.remove(EXTENSIONS_DIRECTORY_PATH)
            else:
                shutil.rmtree(EXTENSIONS_DIRECTORY_PATH)

        if os.path.isdir(self.sample_directory_path):
            shutil.rmtree(self.sample_directory_path)

        if not os.path.isfile(self.sample_extension_path):
            shutil.move(self.temporary_sample_extension_path,
                        self.sample_extension_path)

        self.reinstate_actual_directory_path()

    @property
    def temporary_directory_path(self) -> str:
        return f"{EXTENSIONS_DIRECTORY_PATH}.actual"

    @property
    def temporary_sample_extension_path(self) -> str:
        return f"{self.sample_extension_path}.backup"

    @property
    def sample_directory_path(self) -> str:
        return os.path.join(ARCHIVE_HANDLE_SAMPLES, "sample_chrome_extensions")

    @property
    def sample_extension_path(self) -> str:
        return os.path.join(ARCHIVE_HANDLE_SAMPLES,
                            "sample_extension.crx")

    def create_sample_directory(self) -> str:
        directory_path = self.sample_directory_path
        os.mkdir(directory_path)
        return directory_path

    def rename_actual_directory_path(self):
        if os.path.exists(EXTENSIONS_DIRECTORY_PATH):
            os.rename(EXTENSIONS_DIRECTORY_PATH, self.temporary_directory_path)

    def reinstate_actual_directory_path(self):
        if os.path.exists(self.temporary_directory_path):
            os.rename(self.temporary_directory_path, EXTENSIONS_DIRECTORY_PATH)

    def test_empty_setup(self):
        self.assertFalse(os.path.exists(EXTENSIONS_DIRECTORY_PATH))

        ArchiveHandle.setup()
        self.assertTrue(os.path.exists(EXTENSIONS_DIRECTORY_PATH))
        self.assertTrue(os.path.isdir(EXTENSIONS_DIRECTORY_PATH))

    def test_linked_setup(self):
        sample_directory_path = self.create_sample_directory()
        self.assertTrue(os.path.isdir(sample_directory_path))
        self.assertFalse(os.path.isdir(EXTENSIONS_DIRECTORY_PATH))

        ArchiveHandle.setup(sample_directory_path)
        self.assertTrue(os.path.isdir(EXTENSIONS_DIRECTORY_PATH))

        # Ensure files can be written through the logical link
        link_file_path = os.path.join(EXTENSIONS_DIRECTORY_PATH, "test_file")
        actual_file_path = os.path.join(sample_directory_path, "test_file")
        open(link_file_path, "a").close()
        self.assertTrue(os.path.isfile(link_file_path))
        self.assertTrue(os.path.isfile(actual_file_path))

    def test_get_version_from_manifest(self):
        sample_manifest_path = os.path.join(ARCHIVE_HANDLE_SAMPLES,
                                            "sample_extension",
                                            "manifest.json")
        self.assertTrue(os.path.isfile(sample_manifest_path))
        detected_version = ArchiveHandle.get_version_from_manifest(
            sample_manifest_path
        )
        self.assertEqual(detected_version, "3.2")
