#!/usr/bin/env python
# -*- coding: utf-8 -*-


class ErrorMsg:
    REQUEST_ERROR = 'Request error'
    PERMISSION_DENIED = 'Permission denied'
    PERMISSION_KEY_ERROR = 'No permission named '

    def __init__(self):
        pass


class AccountErrorMsg:
    UNEXPECTED_TOKEN = 'Unexpected token'
    UNEXPECTED_FLAG = 'Unexpected token mark bit'
    TOKEN_TIMEOUT = 'Token timeout'
    PASSWORD_ERROR = 'Username and password do not match'
    DUPLICATE_USERNAME = 'Duplicate username'
    ROLE_PERMISSION_DENIED = 'Role permission denied'
    SIGN_UP_DENIED = 'Sign up denied'

    def __init__(self):
        pass
