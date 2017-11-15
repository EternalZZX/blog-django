#!/usr/bin/env python
# -*- coding: utf-8 -*-

from blog.common.base import Dictable, NoneObject
from blog.common.message import ERROR_MSG, ACCOUNT_ERROR_MSG


class AuthError(Exception, Dictable):
    def __init__(self, error=NoneObject(), code=401, message=ACCOUNT_ERROR_MSG.UNEXPECTED_TOKEN):
        self.code = code or error.code
        self.message = message or error.message


class ServiceError(Exception, Dictable):
    def __init__(self, error=NoneObject(), code=400, message=ERROR_MSG.REQUEST_ERROR):
        self.code = code or error.code
        self.message = message or error.message