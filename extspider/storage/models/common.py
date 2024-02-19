# -*- coding: utf-8 -*-
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.sql import text
from sqlalchemy import create_engine
from abc import ABC as AbstractClass, abstractmethod

TEST_RECORDS_AMOUNT = 10


class BaseModel(DeclarativeBase):
    """
    BaseModel base class from which all other classes mapping the database
    tables will inherit from
    """


class BaseModelTestCase(AbstractClass):

    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        with self.engine.begin() as connection:
            # Ensure foreign key constraints are followed
            connection.execute(text('pragma foreign_keys=on'))

        BaseModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def assertNoResults(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def test_insertion(self):
        pass

    @abstractmethod
    def test_update(self):
        pass

    @abstractmethod
    def test_deletion(self):
        pass

    @abstractmethod
    def test_parameter_validation(self):
        pass
