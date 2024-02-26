# -*- coding: utf-8 -*-
import copy
from typing import Optional, Iterable, Self
from datetime import date
import json
from dataclasses import dataclass, fields, asdict
from extspider.common.utils import is_valid_extension_id
from extspider.common.exception import InvalidExtensionIdentifier


@dataclass(init=True, repr=True, eq=True, slots=True)
class BaseExtensionDetails:
    """The detail of a generic extension scraped from an online store"""
    identifier: str
    name: Optional[str] = None
    version: Optional[str] = None
    last_update: Optional[date] = None
    description: Optional[str] = None
    category: Optional[str] = None
    rating_average: Optional[float] = None
    rating_count: Optional[int] = None
    user_count: Optional[int] = None
    manifest: Optional[dict] = None
    byte_size: Optional[int] = None
    developer_name: Optional[str] = None

    @property
    def download_url(self) -> str:
        raise NotImplementedError

    def __hash__(self):
        data_dict = asdict(self)
        data_dict["manifest"] = json.dumps(self.manifest, sort_keys=True)
        return hash(tuple(data_dict.values()))

    @classmethod
    def get_attribute_index(cls, attribute: str) -> int:
        """Returns the index of the given attribute in the tuple representation
        of the object. If not found, returns -1"""
        for index, field in enumerate(fields(cls)):
            if field.name == attribute:
                return index
        return -1  # Attribute not found

    def __iter__(self):
        for field in fields(self):
            yield getattr(self, field.name)

    def __len__(self):
        return len(fields(self))

    def __post_init__(self):
        if not is_valid_extension_id(self.identifier):
            raise InvalidExtensionIdentifier(f"Invalid identifier in {repr(self)}")

    def update_from(self, details: Iterable) -> None:
        """Update all the fields from a structured Iterable"""
        if len(self) != len(details):
            raise ValueError(
                "update_from() argument does not have enough items; "
                f"expected {len(self)}, received {len(details)}"
            )
        for index, field in enumerate(fields(self)):
            value = details[index]
            if value is not None:
                setattr(self, field.name, value)

    def copy_from(self, other: Self) -> None:
        """Copies all the fields from another instance"""
        if not isinstance(other, type(self)):
            raise TypeError(
                "copy_from() argument must be an instance of the same class"
            )

        for field in fields(self):
            value = getattr(other, field.name)
            if value is not None:
                setattr(self, field.name, value)

    def copy(self):
        """Returns a deep copy of the current instance"""
        return copy.deepcopy(self)

    def download(self, download_path: str) -> None:
        """Download an extension CRX archive in the given path"""
        raise NotImplementedError

    def update_details(self) -> bool:
        """Scrapes the extension's online details

        Returns:
            True if the details were updated, false otherwise.
        """
        raise NotImplementedError

