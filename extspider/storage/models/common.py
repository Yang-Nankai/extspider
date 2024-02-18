# -*- coding: utf-8 -*-
import random
import string
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.sql import text
from sqlalchemy import create_engine
from abc import ABC as AbstractClass, abstractmethod

TEST_RECORDS_AMOUNT = 10


def get_invalid_characters_from_id(id: str) -> str:
    valid_characters = "abcdefghijklmnop"
    unexpected_characters = ""
    for character in id:
        if character not in valid_characters:
            unexpected_characters += character

    return unexpected_characters


def get_random_extension_id() -> str:
    encoded_digits = string.ascii_lowercase[:16]
    return "".join(random.choice(encoded_digits) for _ in range(32))


def is_valid_extension_id(id: str) -> bool:
    # key and id are expected to be the same value
    if len(id) != 32:
        # Expected 32 characters
        return False

    found_invalid_characters = get_invalid_characters_from_id(id)
    if len(found_invalid_characters) > 0:
        # A value different from [a-p] was found
        return False

    return True


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
