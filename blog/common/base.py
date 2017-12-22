#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import memcache
import random
import time
import json

from Crypto.Hash import MD5

from blog.account.users.models import User
from blog.account.roles.models import Role
from blog.common.error import AuthError, ServiceError
from blog.common.message import ErrorMsg, AccountErrorMsg
from blog.common.setting import Setting, PermissionName
from blog.settings import MEMCACHED_HOSTS


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
        if not Setting.SESSION_LIMIT and MemcachedClient().get(key=uuid):
            token = self.update_token(uuid=uuid)
        else:
            rand = MD5.new()
            rand.update(str(random.random()))
            md5 = rand.hexdigest()
            token = base64.b64encode('ETE' + md5 + base64.b64encode(uuid)).rstrip('=')
            self._save_token(uuid=uuid, md5=md5)
        return token

    def update_token(self, token=None, uuid=None, role_id=None):
        if uuid and MemcachedClient().get(key=uuid):
            role_id_stamp, md5_stamp, time_stamp = self._parse_memcached_value(uuid=uuid)
            token = base64.b64encode('ETE' + md5_stamp + base64.b64encode(uuid)).rstrip('=')
        elif token:
            uuid, role_id_stamp, md5_stamp, time_stamp = self._auth_token_md5(token=token)
        else:
            return None
        time_stamp = time_stamp if role_id else None
        role_id = role_id if role_id else role_id_stamp
        if uuid and md5_stamp:
            self._save_token(uuid=uuid, md5=md5_stamp, time_stamp=time_stamp, role_id=role_id)
            return token
        return None

    def auth_token(self, token):
        uuid, role_id, md5_stamp, time_stamp = self._auth_token_md5(token=token)
        if Setting.TOKEN_EXPIRATION and time.time() - int(time_stamp) > Setting.TOKEN_EXPIRATION_TIME:
            MemcachedClient().delete(uuid)
            raise AuthError(code=419, message=AccountErrorMsg.TOKEN_TIMEOUT)
        self._save_token(uuid=uuid, md5=md5_stamp, role_id=role_id)
        return uuid, role_id

    @staticmethod
    def cancel_token(uuid):
        MemcachedClient().delete(key=uuid)

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
    def _save_token(uuid, md5, time_stamp=None, role_id=None):
        if not time_stamp:
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
        perm = {'_role_level': role.role_level}
        for k, v in PermissionName():
            try:
                grant = role.rolepermission_set.get(permission__name=v)
                perm[v] = {'state': grant.state}
                if grant.major_level is not None:
                    perm[v]['major_level'] = int(grant.major_level)
                if grant.minor_level is not None:
                    perm[v]['minor_level'] = int(grant.minor_level)
                if grant.value is not None:
                    perm[v]['value'] = int(grant.value)
            except role.rolepermission.DoesNotExist:
                perm[v] = {'state': False}
        MemcachedClient().set('PERMISSION_' + str(role.id), json.dumps(perm))
        return perm


class Service(object):
    def __init__(self, request):
        self.request = request
        self.token = request.META.get('HTTP_AUTH_TOKEN')
        self.uuid, self.role_id = Authorize().auth_token(self.token)
        self.permission = Grant().get_permission(role_id=self.role_id)
        try:
            self.role_level = self.permission['_role_level']
        except KeyError:
            raise AuthError(code=503, message=ErrorMsg.PERMISSION_KEY_ERROR + '_role_level')

    def has_permission(self, perm_name):
        try:
            if not self.permission[perm_name]['state']:
                raise AuthError(code=403, message=ErrorMsg.PERMISSION_DENIED)
        except KeyError:
            raise AuthError(code=403, message=ErrorMsg.PERMISSION_DENIED)
        return True

    def get_permission_level(self, perm_name):
        self.has_permission(perm_name)
        try:
            major_level = self.permission[perm_name]['major_level']
        except KeyError:
            major_level = 0
        try:
            minor_level = self.permission[perm_name]['minor_level']
        except KeyError:
            minor_level = 0
        return major_level, minor_level

    def get_permission_value(self, perm_name):
        self.has_permission(perm_name)
        try:
            return self.permission[perm_name]['value']
        except KeyError:
            return 0

    @staticmethod
    def is_unique(model_obj, exclude_id=None, **kwargs):
        try:
            if model_obj.objects.exclude(id=exclude_id).get(**kwargs):
                raise ServiceError(message=ErrorMsg.DUPLICATE_IDENTITY)
        except model_obj.MultipleObjectsReturned:
            raise ServiceError(code=500, message=ErrorMsg.DUPLICATE_IDENTITY)
        except model_obj.DoesNotExist:
            return kwargs.values()[0]
