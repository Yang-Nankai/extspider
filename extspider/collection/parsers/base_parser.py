# -*- coding: utf-8 -*-
import abc
from abc import ABC as AbstractClass
from typing import Iterable, Callable, Any, Optional, List
from extspider.common.exception import UnexpectedDataStructure


class DataMapper(AbstractClass):
    """
    Base class for transforming iterable data structures into mapped data.

    Class Attributes:
        INDEX_MAP (dict): Dictionary mapping all the attributes and
            corresponding index paths - e.g. The index path `[0, 0, 1]`
            represents `raw_data[0][0][1]`

    Attributes:
        raw_data (list): List of unprocessed data to be mapped.

    Example:
        ```
        class ChildDataMapper(DataMapper)
            INDEX_MAP = {
                "bool": [1],
                "number": [0, 0, 0],
                "letter": [0, 0, 1]
            }

        raw_data = [[[1, "a"]], False, "discarded"]
        mapper = ChildDataMapper(raw_data)
        print(mapper.to_list())  # Output: [False, 1, "a"]
        print(ChildDataMapper.raw_data_to_list())  # Output: [False, 1, "a"]
        ```
    """
    INVALID_INDEX_PATH = ""

    @property
    @abc.abstractmethod
    def INDEX_MAP(self) -> dict[str, int | list[int]]:
        """
        Maps data attributes to their list index paths.
        !IMPORTANT: Must be implemented in subclasses as class attributes.
        """

    @property
    def DATA_TRANSFORMERS(self) -> dict[str, Callable]:
        """
        Maps **some** data attributes to their transformation functions.
        The data is kept as-is for missing data attributes.
        ?NOTE: This property may be optionally implemented in subclasses
        """
        return {}

    def __init__(self, raw_data: Iterable):
        self.raw_data = list(raw_data)
        if not self.is_data_structure_valid():
            # TODO: 这里的异常需要考虑
            # Raise Unexpected Structure
            pass

    def is_data_structure_valid(self) -> bool:
        sentinel = object()
        for attribute in self.INDEX_MAP.keys():
            index_path = self.get_index_path(attribute)
            raw_data = self.get_raw_data(index_path, default=sentinel)
            if raw_data is sentinel:
                return False
        return True

    def get_index_path(self, attribute_name: str) -> Optional[list[int]]:
        index_path = self.INDEX_MAP.get(attribute_name)
        if index_path is None:
            return None
        # index is either a list or an integer
        return index_path if isinstance(index_path, list) else [index_path]

    def get_data(self, attribute_name: str) -> Any:
        """
        Safely retrieves and transforms a data element given its attribute name.

        Args:
            attribute_name (str): The requested data element
                ?NOTE: Must be defined in INDEX_MAP.

        Returns:
            The tranformed data if the attribute is found in the raw data;
            Otherwise the default value.
        """
        index_path = self.get_index_path(attribute_name)
        if index_path is None:  # The attribute is not in INDEX_MAP
            raise KeyError(f"The attribute '{attribute_name}' is not defined"
                           " in INDEX_MAP")
        raw_data = self.get_raw_data(index_path)
        return self.transform_data(attribute_name, raw_data)

    def get_raw_data(self, index_path: list, default=None) -> Any:
        """
        Safely retrieves a data element given its index path without applying
            any transformation.

        Args:
            index_path (list): Indices to the requested data element.
            default: Returned if index path is invalid (default is None).

        Returns:
            Data at index path or default value.
        """
        current_element = self.raw_data
        for index in index_path:
            try:
                current_element = current_element[index]
            except (IndexError, TypeError):
                return default

        return current_element

    def transform_data(self, attribute_name: str, value: Any) -> Any:
        """
        Transforms a data element given its value and attribute name.
        """
        transformer = self.DATA_TRANSFORMERS.get(attribute_name)
        # TODO: 需要考虑并cleanup!
        # if transformer is None or value is None:
        #     return value
        if transformer is None:
            return value
        return transformer(value)

    def to_list(self) -> List:
        """Returns a list structured as defined by INDEX_MAP."""
        return [self.get_data(attribute_name)
                for attribute_name in self.INDEX_MAP.keys()]

    @classmethod
    def map_data_list(cls, raw_data: Iterable) -> List:
        """Converts raw_data to a list structured as defined by INDEX_MAP."""
        return cls(raw_data).to_list()
