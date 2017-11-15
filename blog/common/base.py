#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import memcache
import random
import time

from Crypto.Hash import MD5
from blog.common.error import AuthError
from blog.common.message import ERROR_MSG
from blog.settings import MEMCACHED_HOSTS, SESSION_LIMIT, \
                          TOKEN_EXPIRATION, TOKEN_EXPIRATION_TIME


class Dictable(object):
    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def dict(self):
        return dict(self)

    def __iter__(self):
        return self.__dict__.items()


class NoneObject(object):
    def __getattr__(self, key):
        return self

    def __or__(self, other):
        return other

    def __and__(self, other):
        return self


class Response(object):
    def __init__(self, code=200, data=None):
        if data is None:
            data = {}
        self.code = code
        self.data = data


class MemcachedClient(object):
    def __init__(self):
        self.client = memcache.Client(MEMCACHED_HOSTS, debug=0)

    def set(self, key, value):
        return self.client.set(key, value)

    def get(self, key):
        return self.client.get(key)

    def replace(self, key, value):
        return self.client.replace(key, value)

    def delete(self, key):
        return self.client.delete(key)


class Authorize(object):
    @staticmethod
    def gen_token(uuid):
        if not SESSION_LIMIT and MemcachedClient().get(key=uuid):
            token = Authorize.update_token(uuid=uuid)
        else:
            rand = MD5.new()
            rand.update(str(random.random()))
            md5 = rand.hexdigest()
            token = base64.b64encode('ETE' + md5 + base64.b64encode(uuid)).rstrip('=')
            Authorize.save_token(uuid=uuid, md5=md5)
        return token

    @staticmethod
    def update_token(token=None, uuid=None):
        if uuid:
            md5_stamp, time_stamp = Authorize.parse_memcached_value(uuid=uuid)
            token = base64.b64encode('ETE' + md5_stamp + base64.b64encode(uuid)).rstrip('=')
        else:
            uuid, md5_stamp = Authorize.parse_token(token=token)
        if uuid and md5_stamp:
            Authorize.save_token(uuid=uuid, md5=md5_stamp)
            return token
        return None

    @staticmethod
    def save_token(uuid, md5):
        time_stamp = str(time.time()).split('.')[0]
        value = md5 + '&' + time_stamp
        MemcachedClient().set(key=uuid, value=value)

    @staticmethod
    def auth_token(token):
        uuid, md5 = Authorize.parse_token(token=token)
        if not uuid:
            raise AuthError()
        md5_stamp, time_stamp = Authorize.parse_memcached_value(uuid=uuid)
        if not md5_stamp:
            raise AuthError()
        if md5_stamp != md5:
            raise AuthError(code=418, message=ERROR_MSG.UNEXPECTED_FLAG)
        if TOKEN_EXPIRATION and time.time() - int(time_stamp) > TOKEN_EXPIRATION_TIME:
            MemcachedClient().delete(uuid)
            raise AuthError(code=419, message=ERROR_MSG.UNEXPECTED_FLAG)
        return uuid

    @staticmethod
    def parse_token(token):
        if len(token) > 4:
            code = token
            num = 4 - (len(token) % 4)
            if num < 4:
                for i in range(num):
                    code += '='
            code = base64.b64decode(code)
            if len(code) > 35 and code[:3] == 'ETE':
                return base64.b64decode(code[35:]), code[3:35]
        return None, None

    @staticmethod
    def parse_memcached_value(uuid):
        value = MemcachedClient().get(key=uuid)
        if not value:
            return None, None
        value_list = value.split('&')
        if len(value_list) != 2:
            return None, None
        return value_list[0], value_list[1]


class Service(object):
    def __init__(self, request):
        self.request = request
        self.token = request.META.get('HTTP_AUTH_TOKEN')
        self.uuid = Authorize.auth_token(self.token)
