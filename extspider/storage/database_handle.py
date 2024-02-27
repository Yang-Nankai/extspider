import os
from datetime import date
from typing import Optional, Dict
from sqlalchemy import create_engine, Engine, and_
from sqlalchemy.orm import scoped_session as ScopedSession, sessionmaker
from sqlalchemy.sql import text

from extspider.common.configuration import DB_PATH
from extspider.storage.models.common import BaseModel
from extspider.storage.models.extension import Extension, ExtensionCategory

DATABASE_NAME = "database.sqlite"
DATABASE_PATH = os.path.join(DB_PATH, DATABASE_NAME)


class DatabaseHandle:
    """
    DatabaseHandle helper class to facilitate and manage connection to the
    database through SQLAlchemy Core
    """

    engine: Engine = None
    Session: ScopedSession = None

    @classmethod
    def setup_engine(cls, absolute_path: str = DATABASE_PATH) -> None:
        if cls.engine is not None:
            return

        cls.engine = create_engine(f"sqlite:///{absolute_path}",
                                   connect_args={"timeout": 60})
        BaseModel.metadata.create_all(cls.engine)
        with cls.engine.begin() as connection:
            # Ensure foreign key constraints are followed
            connection.execute(text('pragma foreign_keys=on'))

        session_factory = sessionmaker(bind=cls.engine)
        cls.Session = ScopedSession(session_factory)  # thread-safe(-ish)
        # still throws errors if
        # concurrency is high

    @classmethod
    def dispose(cls) -> None:
        cls.engine.dispose()

    @classmethod
    def erase(cls) -> None:
        if cls.engine is None:
            return

        engine_url = cls.engine.url.database
        cls.dispose()
        cls.engine = None

        if os.path.isfile(engine_url):
            os.remove(engine_url)

    @classmethod
    def get_session(cls, engine_path: str = DATABASE_PATH) -> ScopedSession:
        cls.setup_engine(engine_path)
        return cls.Session()

    @classmethod
    def get_or_create_extension(cls,
                                session: ScopedSession,
                                extension_id: str,
                                extension_version: str) -> Extension:
        extension = session.query(
            Extension
        ).where(
            and_(
                Extension.id == extension_id,
                Extension.version == extension_version
            )
        ).first()

        if extension is None:
            extension = Extension(extension_id, extension_version)
            session.add(extension)
            session.commit()

        return extension

    @classmethod
    def get_or_create_extension_category(
            cls,
            session: ScopedSession,
            category_name: str
    ) -> ExtensionCategory:

        category = session.query(
            ExtensionCategory
        ).where(ExtensionCategory.name == category_name).first()

        if category is None:
            category = ExtensionCategory(category_name)
            session.add(category)
            session.commit()

        return category

    @classmethod
    def store_extension(cls,
                        extension_id: str,
                        extension_version: str,
                        name: Optional[str],
                        developer_name: Optional[str],
                        category_name: Optional[str],
                        download_count: Optional[int],
                        rating_count: Optional[int],
                        rating_average: Optional[float],
                        manifest: Optional[Dict],
                        byte_size: Optional[int],
                        updated_at: Optional[date]) -> Extension:
        with cls.get_session() as session:
            category_id = None
            if category_name is not None:
                category = cls.get_or_create_extension_category(
                    session,
                    category_name
                )
                category_id = category.id
            extension = Extension(id=extension_id,
                                  version=extension_version,
                                  name=name,
                                  developer_name=developer_name,
                                  category_id=category_id,
                                  download_count=download_count,
                                  rating_count=rating_count,
                                  rating_average=rating_average,
                                  manifest=manifest,
                                  byte_size=byte_size,
                                  updated_at=updated_at)

            session.merge(extension)
            session.commit()

        return extension
