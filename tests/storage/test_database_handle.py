import os
from datetime import date
from unittest import TestCase

from extspider.storage.database_handle import DatabaseHandle
from extspider.common.configuration import DB_PATH
from extspider.storage.models.extension import ExtensionCategory, Extension

DATABASE_NAME = "test_database.sqlite"
DATABASE_PATH = os.path.join(DB_PATH, DATABASE_NAME)


class TestDatabaseHandle(TestCase):

    def setUp(self) -> None:
        DatabaseHandle.setup_engine(DATABASE_PATH)

    def tearDown(self) -> None:
        if DatabaseHandle.engine is not None:
            DatabaseHandle.Session.remove()
            DatabaseHandle.engine.dispose()
            DatabaseHandle.engine = None

        if os.path.isfile(DATABASE_PATH):
            os.remove(DATABASE_PATH)

    def test_setup_engine(self):
        self.assertTrue(os.path.isfile(DATABASE_PATH))

    def test_get_session(self):
        session = DatabaseHandle.get_session()
        self.assertIsNotNone(session)

    def test_erase(self):
        DatabaseHandle.erase()
        self.assertIsNone(DatabaseHandle.engine)
        self.assertFalse(os.path.isfile(DATABASE_PATH))

    def test_get_or_create_extension(self):
        session = DatabaseHandle.get_session()

        created_extension = DatabaseHandle.get_or_create_extension(
            session, "a" * 32, "1.0.0"
        )
        session.commit()

        result = session.query(Extension).all()
        self.assertEqual(result, [created_extension])

        gotten_extension = DatabaseHandle.get_or_create_extension(
            session, "a" * 32, "1.0.0"
        )
        session.commit()

        result = session.query(Extension).all()
        self.assertEqual(result, [gotten_extension])
        self.assertEqual(gotten_extension, created_extension)

    def test_get_or_create_extension_category(self):
        session = DatabaseHandle.get_session()
        test_category_name = "test_category"

        created_category = DatabaseHandle.get_or_create_extension_category(
            session,
            test_category_name
        )
        session.commit()

        result = session.query(ExtensionCategory).all()
        self.assertEqual(result, [created_category])

        gotten_category = DatabaseHandle.get_or_create_extension_category(
            session,
            test_category_name
        )
        session.commit()

        result = session.query(ExtensionCategory).all()
        self.assertEqual(result, [gotten_category])
        self.assertEqual(created_category, gotten_category)
        self.assertEqual(gotten_category.name, test_category_name)

    def test_store_extension(self):
        test_arguments = {
            "id": "a" * 32,
            "version": "1.0.0",
            "name": "Test Extension Name",
            "developer_name": "Test Developer Name",
            "category_name": "test_category",
            "download_count": 100000,
            "rating_count": 1234,
            "rating_average": 3.8,
            "manifest": {"manifest_version": 3, "permissions": ["tabs"]},
            "byte_size": 10000,
            "updated_at": date.today(),
            "download_date": date.today()
        }
        stored_extension = DatabaseHandle.store_extension(
            test_arguments["id"],
            test_arguments["version"],
            test_arguments["name"],
            test_arguments["developer_name"],
            test_arguments["category_name"],
            test_arguments["download_count"],
            test_arguments["rating_count"],
            test_arguments["rating_average"],
            test_arguments["manifest"],
            test_arguments["byte_size"],
            test_arguments["updated_at"],
        )
        with DatabaseHandle.get_session() as session:
            category = DatabaseHandle.get_or_create_extension_category(
                session,
                test_arguments["category_name"]
            )
        self.assertEqual(stored_extension.id,
                         test_arguments["id"])
        self.assertEqual(stored_extension.category_id,
                         category.id)
        self.assertEqual(category.name,
                         test_arguments["category_name"])
        self.assertEqual(stored_extension.download_count,
                         test_arguments["download_count"])
        self.assertEqual(stored_extension.rating_count,
                         test_arguments["rating_count"])
        self.assertEqual(stored_extension.rating_average,
                         test_arguments["rating_average"])
        self.assertEqual(stored_extension.version,
                         test_arguments["version"])

        with DatabaseHandle.get_session() as session:
            selected_extension = DatabaseHandle.get_or_create_extension(
                session, test_arguments["id"], test_arguments["version"]
            )

        self.assertEqual(selected_extension.id, stored_extension.id)

        self.assertEqual(stored_extension.manifest_version,
                         test_arguments["manifest"].get("manifest_version"))
        self.assertEqual(stored_extension.manifest_permissions,
                         test_arguments["manifest"].get("permissions"))
        self.assertIsNone(stored_extension.manifest_optional_permissions,)
        self.assertIsNone(stored_extension.manifest_content_scripts_matches)
        self.assertIsNone(stored_extension.manifest_host_permissions)
        self.assertIsNone(stored_extension.manifest_optional_host_permissions)


