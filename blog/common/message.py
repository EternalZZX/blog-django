#!/usr/bin/env python
# -*- coding: utf-8 -*-


class ErrorMsg:
    SERVER_ERROR = 'Server error'
    SETTING_ERROR = 'Server setting uninitialized'

    REQUEST_ERROR = 'Request error'
    REQUEST_METHOD_ERROR = 'Request method error'
    REQUEST_PARAMS_ERROR = 'Request params error'

    PERMISSION_DENIED = 'Permission denied'
    ORDER_PARAMS_ERROR = 'Order field error'
    ORDER_PERMISSION_DENIED = 'Order field permission denied'
    QUERY_PERMISSION_DENIED = 'Query permission denied'
    PERMISSION_KEY_ERROR = 'No permission named '

    DUPLICATE_IDENTITY = 'Duplicate identity field'

    def __init__(self):
        pass


class AccountErrorMsg:
    UNEXPECTED_TOKEN = 'Unexpected token'
    UNEXPECTED_FLAG = 'Unexpected token marks bit'
    TOKEN_TIMEOUT = 'Token timeout'
    PASSWORD_ERROR = 'Username and password do not match'

    USER_NOT_FOUND = 'User not found'
    ROLE_NOT_FOUND = 'Role not found'
    UPDATE_PERMISSION_DENIED = 'Update permission denied'

    ROLE_PERMISSION_DENIED = 'Role permission denied'
    NO_DEFAULT_ROLE = 'Default role is not exists'
    PERMISSION_JSON_ERROR = 'Permission JSON syntax error'

    SIGN_UP_DENIED = 'Sign up denied'

    def __init__(self):
        pass


class ContentErrorMsg:
    ALBUM_NOT_FOUND = 'Album not found'
    ARTICLE_NOT_FOUND = 'Article not found'
    PHOTO_NOT_FOUND = 'Photo not found'
    PHOTO_LIMIT_EXCEED = 'Photo limit exceed'
    SECTION_NOT_FOUND = 'Section not found'
    SECTION_PERMISSION_DENIED = 'Section permission denied'
    STATUS_PERMISSION_DENIED = 'Status permission denied'
    RESOURCE_NOT_FOUND = 'Resource not found'

    def __init__(self):
        pass
