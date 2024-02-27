"""
archive_handle abstraction layer to manage extension archives in a directory
tree, structured as follows.

./data
└── chrome_extensions/
    ├── <EXTENSION_ID>/        # extension identifier
    │   ├── unknown/           # unprocessed/corrupted archives
    │   │   ├── <EXTENSION_ID>.<UNKNOWN>.crx
    │   │   └── ...
    │   ├── <VERSION>/         # version release
    │   │   ├── <EXTENSION_ID>.<VERSION>.crx   # processed archive
    │   │   └── <EXTENSION_ID>.<VERSION>.json  # manifest
    │   └── ...
    └── ...
"""
from typing import Optional, Dict
import json
import os
from pathlib import Path
from extspider.common.configuration import STORAGE_PATH
from extspider.storage.crx_archive import CrxArchive

EXTENSIONS_DIRECTORY_NAME = "chrome_extensions"
EXTENSIONS_DIRECTORY_PATH = os.path.join(STORAGE_PATH,
                                         EXTENSIONS_DIRECTORY_NAME)


class ExtensionHandle:
    """
    ExtensionHandle abstraction layer to download and manage extension archives
    in the file system
    """

    @classmethod
    def setup(cls, storage_path: Optional[str] = None) -> None:
        """
        setup if a valid storage path is provided, creates a logical link to
        it from a predefined path; Otherwise creates the predefined directory

        Args:
            storage_path (Optional[str]): alternative path for storing
            extension archives
        """
        if Path(EXTENSIONS_DIRECTORY_PATH).is_dir():
            return

        if storage_path is None or not Path(storage_path).is_dir():
            Path(EXTENSIONS_DIRECTORY_PATH).mkdir(parents=True)
        else:
            Path(storage_path).symlink_to(EXTENSIONS_DIRECTORY_PATH)

    @classmethod
    def get_extension_storage_directory(cls, extension_id: str, version_name: str) -> str:
        extension_path = Path(EXTENSIONS_DIRECTORY_PATH) / extension_id

        if version_name is None:
            version_name = "UNKNOWN"

        return str(extension_path / version_name)

    @classmethod
    def get_extension_storage_path(cls, identifier: str, version: str) -> str:
        """
        get_extension_storage_path

        Args:
            identifier (str): an extension identifier
            version (str): the version of the extension

        Returns:
            str: the directory path where the extension release is stored
        """
        storage_directory = cls.get_extension_storage_directory(identifier, version)
        return str(Path(storage_directory) / f'{identifier}.{version}.crx')

    @classmethod
    def store_extension_archive(cls,
                                extension_id: str,
                                crx_path: str) -> CrxArchive:
        """
        store_extension_archive extracts a crx archive, stores it in the
        correct directory path, and saves its metadata in the database

        Args:
            extension_id (str): an extension identifier
            crx_path (str): the directory path to the archive to be stored

        Returns:
            CrxArchive: wrapper class containing the archive metadata
        """
        crx_archive = CrxArchive(extension_id, crx_path)
        archive_version = crx_archive.extract_version_from_crx()
        storage_path = cls.get_archive_storage_path(extension_id,
                                                    archive_version)
        os.makedirs(storage_path, exist_ok=True)
        crx_archive.move(storage_path)

        return crx_archive

    @staticmethod
    def get_manifest_dict(manifest_path: str) -> Dict:
        """
        get_manifest_dict

        Args:
            manifest_path (str): path to a `manifest.json` file

        Returns:
            Dict: content of the given manifest converted to python dictionary
        """
        with open(manifest_path, "r") as file:
            return json.load(file)

    @classmethod
    def get_version_from_manifest(cls, manifest_path: str) -> Optional[str]:
        """
        get_version_from_manifest

        Args:
            manifest_path (str): the path to a `manifest.json` file

        Returns:
            Optional[str]: the extension version release extracted from the
            manifest; None if manifest is not found, or corrupted
        """
        return cls.get_manifest_dict(manifest_path).get("version")

    @classmethod
    def get_archive_version_from_directory(cls, directory: str) \
            -> Optional[str]:
        """
        get_archive_version_from_directory

        Args:
            directory (str): directory path containing an extracted extension
            archive

        Returns:
            Optional[str]: the `version` value read from the `manifest.json`
            file located in the given directory
        """
        manifest_path = os.path.join(directory, "manifest.json")
        return cls.get_version_from_manifest(manifest_path)

    @classmethod
    def extract_archive(cls, extension_id, crx_path) -> bool:
        crx = cls.store_extension_archive(extension_id, crx_path)

        if crx.is_corrupted:
            return False

        try:
            zip = crx.get_zip_archive()
            zip.extractall(
                os.path.join(
                    crx.base_directory,
                    crx.digest
                ))
        except Exception:
            return False

        return True
