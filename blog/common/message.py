#!/usr/bin/env python
# -*- coding: utf-8 -*-


class ErrorMsg:
    SERVER_ERROR = 'Server error'
    SETTING_ERROR = 'Server setting uninitialized'

    REQUEST_ERROR = 'Request error'
    REQUEST_METHOD_ERROR = 'Request method error'
    REQUEST_PARAMS_ERROR = 'Request params error'

    PERMISSION_DENIED = 'Permission denied'
    ORDER_PERMISSION_DENIED = 'Order field permission denied'
    QUERY_PERMISSION_DENIED = 'Query permission denied'
    PERMISSION_KEY_ERROR = 'No permission named '

    DUPLICATE_IDENTITY = 'Duplicate identity field'

    def __init__(self):
        pass


class AccountErrorMsg:
    UNEXPECTED_TOKEN = 'Unexpected token'
    UNEXPECTED_FLAG = 'Unexpected token mark bit'
    TOKEN_TIMEOUT = 'Token timeout'
    PASSWORD_ERROR = 'Username and password do not match'

    USER_NOT_FOUND = 'User not found'
    ROLE_NOT_FOUND = 'Role not found'
    UPDATE_PERMISSION_DENIED = 'Update permission denied'

    ROLE_PERMISSION_DENIED = 'Role permission denied'
    NO_DEFAULT_ROLE = 'User of this role exists and default role is not set'
    PERMISSION_JSON_ERROR = 'Permission JSON syntax error'

    SIGN_UP_DENIED = 'Sign up denied'

    def __init__(self):
        pass
