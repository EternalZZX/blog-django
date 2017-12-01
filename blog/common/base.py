#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import memcache
import random
import time
import json

from Crypto.Hash import MD5

from blog.account.models import User, Role
from blog.common.error import AuthError
from blog.common.message import AccountErrorMsg
from blog.common.utils import model_to_dict
from blog.common.permission import PermissionName
from blog.settings import MEMCACHED_HOSTS, SESSION_LIMIT, \
                          TOKEN_EXPIRATION, TOKEN_EXPIRATION_TIME


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
    def gen_token(self, uuid):
        if not SESSION_LIMIT and MemcachedClient().get(key=uuid):
            token = self.update_token(uuid=uuid)
        else:
            rand = MD5.new()
            rand.update(str(random.random()))
            md5 = rand.hexdigest()
            token = base64.b64encode('ETE' + md5 + base64.b64encode(uuid)).rstrip('=')
            self._save_token(uuid=uuid, md5=md5)
        return token

    def update_token(self, token=None, uuid=None):
        if uuid:
            role_id, md5_stamp, time_stamp = self._parse_memcached_value(uuid=uuid)
            token = base64.b64encode('ETE' + md5_stamp + base64.b64encode(uuid)).rstrip('=')
        else:
            uuid, role_id, md5_stamp, time_stamp = self._auth_token_md5(token=token)
        if uuid and md5_stamp:
            self._save_token(uuid=uuid, md5=md5_stamp, role_id=role_id)
            return token
        return None

    def auth_token(self, token):
        uuid, role_id, md5_stamp, time_stamp = self._auth_token_md5(token=token)
        if TOKEN_EXPIRATION and time.time() - int(time_stamp) > TOKEN_EXPIRATION_TIME:
            MemcachedClient().delete(uuid)
            raise AuthError(code=419, message=AccountErrorMsg.TOKEN_TIMEOUT)
        self._save_token(uuid=uuid, md5=md5_stamp, role_id=role_id)
        return uuid, role_id

    def _auth_token_md5(self, token):
        uuid, md5 = self._parse_token(token=token)
        if not uuid:
            raise AuthError()
        role_id, md5_stamp, time_stamp = self._parse_memcached_value(uuid=uuid)
        if not md5_stamp:
            raise AuthError()
        if md5_stamp != md5:
            raise AuthError(code=418, message=AccountErrorMsg.UNEXPECTED_FLAG)
        return uuid, role_id, md5_stamp, time_stamp

    @staticmethod
    def _save_token(uuid, md5, role_id=None):
        time_stamp = str(time.time()).split('.')[0]
        if not role_id:
            try:
                role_id = User.objects.get(uuid=uuid).role.id
            except User.DoesNotExist:
                raise AuthError()
        value = md5 + '&' + time_stamp + '&' + str(role_id)
        MemcachedClient().set(key=uuid, value=value)

    @staticmethod
    def _parse_token(token):
        if token and len(token) > 4:
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
    def _parse_memcached_value(uuid):
        value = MemcachedClient().get(key=uuid)
        if not value:
            return None, None, None
        value_list = value.split('&')
        if len(value_list) != 3:
            return None, None, None
        [md5_stamp, time_stamp, role_id] = value_list
        return role_id, md5_stamp, time_stamp


class Grant(object):
    def load_permission(self):
        roles = Role.objects.all()
        for role in roles:
            self.set_permission(role=role)

    def get_permission(self, role_id):
        value = MemcachedClient().get(key='PERMISSION_' + str(role_id))
        if value:
            return json.loads(value)
        else:
            return self.set_permission(role_id=role_id)

    @staticmethod
    def set_permission(role_id=None, role=None):
        if not role:
            try:
                role = Role.objects.get(id=role_id)
            except Role.DoesNotExist:
                return None
        perm = {}
        for k, v in PermissionName():
            try:
                grant = role.rolepermission_set.get(permission__name=v)
                perm[k] = {
                    'state': grant.state,
                    'level': grant.level,
                    'value': grant.value
                }
            except role.rolepermission.DoesNotExist:
                perm[k] = {
                    'state': False,
                    'level': None,
                    'value': None
                }
        MemcachedClient().set('PERMISSION_' + str(role.id), json.dumps(perm))
        return perm


class Service(object):
    def __init__(self, request):
        self.request = request
        self.token = request.META.get('HTTP_AUTH_TOKEN')
        self.uuid, self.role_id = Authorize().auth_token(self.token)
        self.permission = Grant().get_permission(role_id=self.role_id)
