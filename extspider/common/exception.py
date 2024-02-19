# -*- coding: utf-8 -*-

class extSpiderBaseException(Exception):
    pass


class InvalidExtensionIdentifier(extSpiderBaseException):
    pass


class CategoryCollectionError(extSpiderBaseException):
    pass


class CategoryRequestError(extSpiderBaseException):
    pass


class ExtensionRequestDetailError(extSpiderBaseException):
    pass


class InvalidCategoryResponse(extSpiderBaseException):
    pass


class ExtensionDownloadExtensionError(extSpiderBaseException):
    pass


class UnexpectedDataStructure(ValueError):
    """
    Raised when an unprocessed data list does not adhere to the structure
    defined by a DataMapper's INDEX_MAP.
    """