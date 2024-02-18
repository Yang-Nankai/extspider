import os
import shutil
from glob import glob
from unittest import TestCase, skipIf, skip

from extspider.storage.crx_archive import CrxArchive, BadCrx
from extspider.common.context import ASSETS_PATH, TEST_SAMPLES_PATH

SAMPLES_ROOT = os.path.join(TEST_SAMPLES_PATH, "crx_archive")
SAMPLE_ARCHIVE_PATH = os.path.join(SAMPLES_ROOT,
                                   "sample_extension.crx")
SAMPLE_ARCHIVE_TEMPORARY = f"{SAMPLE_ARCHIVE_PATH}.temporary"
EXTENSIONS_ROOT = os.path.join(ASSETS_PATH, "chrome_extensions")


def get_downloaded_archives() -> list[str]:
    return glob(f"{EXTENSIONS_ROOT}/**/*.crx", recursive=True)


class TestCrxArchive(TestCase):

    def setUp(self) -> None:
        shutil.copy(SAMPLE_ARCHIVE_PATH,
                    SAMPLE_ARCHIVE_TEMPORARY)

    def tearDown(self) -> None:
        for sample_archive in glob(f"{SAMPLES_ROOT}/*.crx"):
            os.remove(sample_archive)

        if os.path.isfile(f"{SAMPLES_ROOT}/manifest.json"):
            os.remove(f"{SAMPLES_ROOT}/manifest.json")

        shutil.move(SAMPLE_ARCHIVE_TEMPORARY,
                    SAMPLE_ARCHIVE_PATH)

    def get_sample_archive(self, custom_name: str = None) -> CrxArchive:
        sample_id = "a" * 32
        archive = CrxArchive(sample_id, SAMPLE_ARCHIVE_PATH,
                             custom_name=custom_name)
        archive.load_manifest()
        archive.load_namelist()
        return archive

    def test_archive_creation(self):
        archive = self.get_sample_archive()
        self.assertIsNotNone(archive.json_manifest)
        self.assertEqual(type(archive.json_manifest), dict)
        self.assertGreater(len(archive.archive_namelist), 0)

    def test_custom_name(self):
        custom_name = "test_archive.crx"
        archive = self.get_sample_archive(custom_name)
        base_directory = archive.base_directory
        expected_path = os.path.join(base_directory, custom_name)
        archive_exists = os.path.isfile(expected_path)
        self.assertTrue(archive_exists)

    def test_wildcard_to_paths(self):
        archive = self.get_sample_archive()
        resources = archive.json_manifest.get("web_accessible_resources")

        self.assertEqual(type(resources), list)

        paths = archive.wildcard_to_paths("images/*")
        self.assertGreater(len(paths), 0)

    def test_process_resource(self):
        archive = self.get_sample_archive()
        resources = archive.json_manifest.get("web_accessible_resources")

        self.assertEqual(type(resources), list)

        wildcard_paths = archive.process_resource("/images/*")
        self.assertGreater(len(wildcard_paths), 0)

        defined_paths = archive.process_resource("/js/page/fetchAngular.js")
        self.assertEqual(len(defined_paths), 1)

        non_existing_paths = archive.process_resource("/this/does/not/exist.css")
        self.assertEqual(len(non_existing_paths), 0)

    def test_extract_fingerprints(self):
        archive = self.get_sample_archive()
        fingerprints = archive.extract_fingerprints()

        self.assertTrue(isinstance(fingerprints, list))
        self.assertGreater(len(fingerprints), 0)

    @skipIf(len(get_downloaded_archives()) == 0, "No archives found.")
    def test_extract_fingerprints_big(self):
        test_id = "a" * 32
        archive_paths = get_downloaded_archives()
        for crx_path in archive_paths:
            crx = CrxArchive(test_id, crx_path)

            try:
                fingerprints = crx.extract_fingerprints()
            except BadCrx:
                self.assertTrue(crx.is_corrupted)
                continue

            self.assertTrue(isinstance(fingerprints, list))
            manifest: dict = crx.json_manifest
            if manifest is None:
                self.assertTrue(crx.is_corrupted)
                continue

            self.assertTrue(isinstance(manifest, dict))
            manifest_version = manifest.get("manifest_version")
            self.assertIsNotNone(manifest_version)

            resource_list = manifest.get("web_accessible_resources")

            if resource_list is None or len(resource_list) == 0:
                self.assertEqual(len(fingerprints), 0)

            else:
                self.assertGreaterEqual(len(fingerprints), 0)
                if len(fingerprints) == 0:
                    for resource in resource_list:
                        if isinstance(resource, str):
                            self.assertEqual(manifest_version, 2)
                            mv2_resources = resource
                            self.assertFalse(any(crx.is_in_archive(resource)
                                                 for resource
                                                 in mv2_resources))
                            continue

                        self.assertTrue(isinstance(resource, dict))
                        self.assertEqual(manifest_version, 3)

                        resources = resource.get("resources")
                        matches = resource.get("matches")

                        self.assertTrue(
                            (resources is None or len(resources) == 0)
                            or (matches is None or len(matches) == 0)
                            or not any(crx.is_in_archive(resource)
                                       for resource
                                       in resources)
                        )
                else:
                    for resource, match in fingerprints:
                        self.assertTrue(match is None
                                        or isinstance(match, str))
                        self.assertTrue(crx.is_in_archive(resource))
