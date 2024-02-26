# -*- coding: utf-8 -*-

class extSpiderBaseException(Exception):
    pass


class RequestError(extSpiderBaseException):
    pass


class CategoryRequestDetailsError(RequestError):
    pass


class CategoryRequestTypesError(RequestError):
    pass


class InvalidCategoryResponseFormat(extSpiderBaseException):
    pass


class InvalidExtensionIdentifier(extSpiderBaseException):
    pass





class ExtensionRequestDetailError(extSpiderBaseException):
    pass





class ExtensionDownloadExtensionError(extSpiderBaseException):
    pass


class UnexpectedDataStructure(ValueError):
    """
    Raised when an unprocessed data list does not adhere to the structure
    defined by a DataMapper's INDEX_MAP.
    """