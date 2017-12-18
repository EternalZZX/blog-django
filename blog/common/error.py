#!/usr/bin/env python
# -*- coding: utf-8 -*-

from blog.common.utils import Dictable, NoneObject
from blog.common.message import ErrorMsg, AccountErrorMsg


class ServerError(Exception, Dictable):
    def __init__(self, error=NoneObject(), code=500, message=ErrorMsg.SERVER_ERROR):
        self.code = code or error.code
        self.message = message or error.message


class ParamsError(Exception, Dictable):
    def __init__(self, error=NoneObject(), code=400, message=ErrorMsg.REQUEST_PARAMS_ERROR):
        self.code = code or error.code
        self.message = message or error.message


class AuthError(Exception, Dictable):
    def __init__(self, error=NoneObject(), code=401, message=AccountErrorMsg.UNEXPECTED_TOKEN):
        self.code = code or error.code
        self.message = message or error.message


class ServiceError(Exception, Dictable):
    def __init__(self, error=NoneObject(), code=400, message=ErrorMsg.REQUEST_ERROR):
        self.code = code or error.code
        self.message = message or error.message
