#!/usr/bin/env python
# -*- coding: utf-8 -*-


class _Const(object):
    class ConstError(TypeError):
        pass

    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise self.ConstError("Cannot change const %s" % name)
        self.__dict__[name] = value


ERROR_MSG = _Const()

ERROR_MSG.UNEXPECTED_TOKEN = 'Unexpected token'
ERROR_MSG.UNEXPECTED_FLAG = 'Unexpected token mark bit'
ERROR_MSG.REQUEST_ERROR = 'Request error'

ACCOUNT_ERROR_MSG = _Const()
ACCOUNT_ERROR_MSG.DUPLICATE_USERNAME = 'Duplicate username'