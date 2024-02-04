# -*- coding: utf-8 -*-

class extSpiderBaseException(Exception):
    pass

class InvalidExtensionIdentifier(extSpiderBaseException):
    pass

class CategoryCollectionError(extSpiderBaseException):
    pass

class CategoryRequestError(extSpiderBaseException):
    pass

class ExtensionRequestError(extSpiderBaseException):
    pass