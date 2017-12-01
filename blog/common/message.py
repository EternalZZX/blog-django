#!/usr/bin/env python
# -*- coding: utf-8 -*-


class ErrorMsg:
    REQUEST_ERROR = 'Request error'

    def __init__(self):
        pass


class AccountErrorMsg:
    UNEXPECTED_TOKEN = 'Unexpected token'
    UNEXPECTED_FLAG = 'Unexpected token mark bit'
    TOKEN_TIMEOUT = 'Token timeout'
    PASSWORD_ERROR = 'Username and password do not match'
    DUPLICATE_USERNAME = 'Duplicate username'

    def __init__(self):
        pass
