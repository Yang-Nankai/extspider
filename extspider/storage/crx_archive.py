import base64
import json
import shutil
import os
import struct
from zipfile import ZipFile, BadZipFile
from typing import Optional, List, Set
from hashlib import md5, sha256
from io import BufferedReader, BytesIO
from fnmatch import fnmatch

from extspider.storage.database_handle import DatabaseHandle


class BadCrx(IOError):
    pass


class CrxArchive:
    # TODO: 这个类是否还有必要，我只做permission的工作，只需要存储extension的信息即可
    # 但是这里没必要去删除
    BUFFER_SIZE = 65536  # 64kb

    def __init__(self, extension_id: str, crx_path: str,
                 custom_name: str = None) -> None:
        self.crx_path = crx_path
        self.extension_id = extension_id
        self.digest = None # TODO: digest没有必要了
        self.is_corrupted = None  # TODO: is_corrupted是否有必要？
        self.json_manifest = None
        self.archive_namelist = None
        self.custom_name = custom_name

        self.setup()

    def __repr__(self) -> str:
        return (
            f"CrxArchive(crx_path={self.crx_path!r},"
            f"extension_id={self.extension_id!r},"
            f"digest={self.digest!r},"
            f"is_corrupted={self.is_corrupted!r})"
        )

    def setup(self) -> None:
        self.digest = self.compute_digest(self.crx_path)
        self.update_name()

    @property
    def base_directory(self) -> str:
        return os.path.dirname(self.crx_path)

    @base_directory.setter
    def base_directory(self, value: str) -> None:
        self.crx_path = os.path.join(value, self.crx_name)

    @property
    def crx_name(self) -> str:
        if self.custom_name is not None:
            return self.custom_name
        return f"{self.digest}.crx"

    @property
    def manifest_path(self) -> str:
        return os.path.join(self.base_directory, "manifest.json")

    @property
    def byte_size(self) -> int:
        return os.path.getsize(self.crx_path)

    @property
    def crx_bytes(self) -> bytes:
        with open(self.crx_path, 'rb') as file:
            return file.read()

    def compute_digest(self, path: str) -> str:
        hasher = md5()
        with open(path, "rb") as file_bytes:
            while True:
                block = file_bytes.read(self.BUFFER_SIZE)
                if not block:
                    break
                hasher.update(block)
        return hasher.hexdigest()

    def rename(self, new_name: str) -> None:
        new_path = os.path.join(self.base_directory, new_name)
        os.rename(self.crx_path, new_path)
        self.crx_path = new_path

    def update_name(self):
        current_name = os.path.basename(self.crx_path)
        if current_name != self.crx_name:
            self.rename(self.crx_name)

    def is_archive_in_directory(self, directory: str) -> bool:
        archive_path = os.path.join(directory, self.crx_name)
        return os.path.isfile(archive_path)

    def delete_crx(self) -> None:
        try:
            os.remove(self.crx_path)
        except FileNotFoundError:
            pass

    def delete_manifest(self) -> None:
        try:
            os.remove(self.manifest_path)
        except FileNotFoundError:
            pass

    def delete(self) -> None:
        self.delete_crx()
        self.delete_manifest()

    def move_crx_if_exists(self, destination: str) -> None:
        if os.path.isfile(self.crx_path):
            shutil.move(self.crx_path, destination)

    def move_manifest_if_exists(self, destination: str) -> None:
        if os.path.isfile(self.manifest_path):
            shutil.move(self.manifest_path, destination)

    def move(self, destination: str) -> None:
        if self.is_archive_in_directory(destination):
            # delete duplicate
            self.delete()
        else:
            self.move_crx_if_exists(destination)
            self.move_manifest_if_exists(destination)

        self.base_directory = destination

    def save_metadata(self) -> None:
        fingerprints = self.extract_fingerprints()
        DatabaseHandle.store_archive(self.extension_id,
                                     self.digest,
                                     self.json_manifest,
                                     self.is_corrupted,
                                     self.byte_size,
                                     fingerprints)

    def wildcard_to_paths(self, wildcard: str) -> list[str]:
        matches = list()
        for located_path in self.archive_namelist:
            if located_path[-1] != "/" and fnmatch(located_path, wildcard):
                matches.append(located_path)

        return matches

    def is_wildcard(self, path: str) -> bool:
        return any(wildcard_character in path
                   for wildcard_character in ["*", "?"])

    def is_in_archive(self, path: str) -> bool:
        for located_path in self.archive_namelist:
            if path == located_path:
                return True

        return False

    def process_resource(self, resource: str) -> list[str]:

        resource = resource.strip("/")

        if self.is_wildcard(resource):
            return self.wildcard_to_paths(resource)
        elif self.is_in_archive(resource):
            return [resource]
        else:
            return list()

    def process_resources(self, resources: list[str]) -> list[str]:
        processed_resources = list()

        for resource in resources:
            process_results = self.process_resource(resource)
            processed_resources.extend(process_results)

        return processed_resources

    def combine_resources_to_matches(
            self,
            resources: list[str],
            matches: Optional[list[str]]
    ) -> list[tuple[str, Optional[str]]]:

        if matches is None or len(matches) == 0:
            return [(resource, None) for resource in resources]

        resource_match_tuples = list()

        for resource in resources:
            for match in matches:
                resource_match_tuples.append((resource, match))

        return resource_match_tuples

    def process_v2_resources(self,
                             resources: list[str]) -> list[tuple[str, None]]:
        processed_resources = self.process_resources(resources)
        return self.combine_resources_to_matches(processed_resources, None)

    def process_v3_resource(self, resource_dict: dict) -> list[tuple[str, str]]:
        resources = resource_dict.get("resources")
        matches = resource_dict.get("matches")

        processed_resources = self.process_resources(resources)
        return self.combine_resources_to_matches(processed_resources, matches)

    def process_v3_resources(self,
                             resources: list[dict]) -> list[tuple[str, str]]:
        processed_resources = list()
        for resource in resources:
            if not isinstance(resource, dict):
                continue

            process_result = self.process_v3_resource(resource)
            processed_resources.extend(process_result)

        return processed_resources

    def extract_fingerprints(self) -> list[tuple[str, Optional[str]]]:
        if self.json_manifest is None and not self.is_corrupted:
            self.load_manifest()

        if self.archive_namelist is None and not self.is_corrupted:
            self.load_namelist()

        if self.is_corrupted:
            return list()

        manifest_version = self.json_manifest.get("manifest_version")
        resources = self.json_manifest.get("web_accessible_resources")

        if resources is None or manifest_version is None:
            return list()

        if manifest_version == 3:
            return self.process_v3_resources(resources)
        else:
            return self.process_v2_resources(resources)

    def load_namelist(self) -> None:
        zip_file = self.get_zip_archive()

        if zip_file is not None:
            self.archive_namelist = zip_file.namelist()
            del zip_file
        else:
            self.archive_namelist = list()

    def get_zip_archive(self) -> Optional[ZipFile]:
        with open(self.crx_path, "rb") as crx_file:
            try:
                self.strip_crx_headers(crx_file)
                zip_file = ZipFile(
                    BytesIO(crx_file.read())
                )

            except (BadZipFile, BadCrx):
                self.is_corrupted = True
                return None

        self.is_corrupted = False
        return zip_file

    def extract_manifest(self) -> str:
        zip_file = self.get_zip_archive()
        if zip_file is not None:
            zip_file.extract("manifest.json", self.base_directory)
            del zip_file

    def load_manifest(self) -> None:
        if not os.path.isfile(self.manifest_path):
            self.extract_manifest()

        if not self.is_corrupted:
            with open(self.manifest_path, "r") as manifest_file:
                self.json_manifest = json.load(manifest_file)

    def extract_version_from_crx(self) -> str:
        if self.is_corrupted:
            return "corrupted"

        if self.json_manifest is None:
            self.load_manifest()
            return self.extract_version_from_crx()

        return self.get_display_version()

    def get_display_version(self) -> Optional[str]:
        version_name = self.json_manifest.get("version_name")
        if version_name is not None:
            return version_name
        else:
            return self.json_manifest.get("version")

    @staticmethod
    def validate_crx_headers(crx_bytes: bytes) -> None:
        """Raises a BadCrx error if the headers are not valid."""
        # Define the magic numbers for CRX and ZIP files as byte strings
        CRX_MAGIC = b'Cr24'
        ZIP_MAGIC = b'PK\x03\x04'

        # Check if the input is a ZIP file instead of a CRX file
        if crx_bytes.startswith(ZIP_MAGIC):
            raise BadCrx('Input is not a CRX file, but a ZIP file.')

        # Check if the file does not start with 'Cr24' (CRX_MAGIC)
        if not crx_bytes.startswith(CRX_MAGIC):
            raise BadCrx('Invalid header: Does not start with Cr24')

        # Validate the crx format version number
        if crx_bytes[4] not in [2, 3] or any(crx_bytes[5:8]):
            raise BadCrx(f'Unexpected crx format version number: {crx_bytes[4]}')

    @staticmethod
    def assert_magic_number(crx_bytes: bytes) -> None:
        magic_number = crx_bytes.decode("utf-8")
        if magic_number != "Cr24":
            raise BadCrx(f"'Unexpected magic number: {magic_number}.")

    # TODO: This function is same to `little_endian_bytes_to_integer`
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

    @classmethod
    def strip_crx_headers(cls, crx_file: BufferedReader) -> None:
        magic_number_bytes = crx_file.read(4)
        version_bytes = crx_file.read(4)

        cls.assert_magic_number(magic_number_bytes)
        if cls.get_crx_version(version_bytes) <= 2:
            cls.strip_crx2(crx_file)
        else:
            cls.strip_crx3(crx_file)
