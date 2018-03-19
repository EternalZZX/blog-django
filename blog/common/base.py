#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import redis
import memcache
import random
import time
import json

from Crypto.Hash import MD5

from blog.account.users.models import User
from blog.account.roles.models import Role, RolePermission
from blog.common.error import AuthError, ServiceError
from blog.common.message import ErrorMsg, AccountErrorMsg
from blog.common.setting import Setting, PermissionName, PermissionLevel, AuthType
from blog.settings import REDIS_HOSTS, MEMCACHED_HOSTS


class RedisClient(object):
    def __init__(self):
        pool = redis.ConnectionPool(host=REDIS_HOSTS, port=6379, db=0)
        self.client = redis.Redis(connection_pool=pool)

    def set(self, name, value):
        return self.client.set(name, value)

    def get(self, name):
        return self.client.get(name)

    def delete(self, name):
        return self.client.delete(name)

    def hash_set(self, name, key, value):
        return self.client.hset(name, key, value)

    def hash_get(self, name, key):
        return self.client.hget(name, key)

    def hash_delete(self, name, key):
        return self.client.hdel(name, key)


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
        if not Setting().SESSION_LIMIT and MemcachedClient().get(key=uuid):
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
            user_id, role_id_stamp, md5_stamp, time_stamp = self._parse_memcached_value(uuid=uuid)
            token = base64.b64encode('ETE' + md5_stamp + base64.b64encode(uuid)).rstrip('=')
        elif token:
            uuid, user_id, role_id_stamp, md5_stamp, time_stamp = self._auth_token_md5(token=token)
        else:
            return None
        time_stamp = time_stamp if role_id else None
        role_id = role_id if role_id else role_id_stamp
        if uuid and md5_stamp:
            self._save_token(uuid=uuid,
                             md5=md5_stamp,
                             time_stamp=time_stamp,
                             user_id=user_id,
                             role_id=role_id)
            return token
        return None

    def auth_token(self, token):
        uuid, user_id, role_id, md5_stamp, time_stamp = self._auth_token_md5(token=token)
        if Setting().TOKEN_EXPIRATION and time.time() - int(time_stamp) > Setting().TOKEN_EXPIRATION_TIME:
            MemcachedClient().delete(uuid)
            raise AuthError(code=419, message=AccountErrorMsg.TOKEN_TIMEOUT)
        self._save_token(uuid=uuid, md5=md5_stamp, user_id=user_id, role_id=role_id)
        return uuid, user_id, role_id

    @staticmethod
    def cancel_token(uuid):
        MemcachedClient().delete(key=uuid)

    def _auth_token_md5(self, token):
        uuid, md5 = self._parse_token(token=token)
        if not uuid:
            raise AuthError()
        user_id, role_id, md5_stamp, time_stamp = self._parse_memcached_value(uuid=uuid)
        if not md5_stamp:
            raise AuthError()
        if md5_stamp != md5:
            raise AuthError(code=418, message=AccountErrorMsg.UNEXPECTED_FLAG)
        return uuid, user_id, role_id, md5_stamp, time_stamp

    @staticmethod
    def _save_token(uuid, md5, time_stamp=None, user_id=None, role_id=None):
        if not time_stamp:
            time_stamp = str(time.time()).split('.')[0]
        if not user_id or not role_id:
            try:
                user = User.objects.get(uuid=uuid)
                user_id = user.id
                role_id = user.role.id
            except User.DoesNotExist:
                raise AuthError()
        if not user_id or not role_id:
            raise AuthError()
        value = md5 + '&' + time_stamp + '&' + str(user_id) + '&' + str(role_id)
        MemcachedClient().set(key=uuid, value=value)

    @staticmethod
    def _parse_token(token):
        if token and len(token) > 4:
            code = token
            num = 4 - (len(token) % 4)
            if num < 4:
                for i in range(num):
                    code += '='
            try:
                code = base64.b64decode(code)
            except TypeError:
                return None, None
            if len(code) > 35 and code[:3] == 'ETE':
                return base64.b64decode(code[35:]), code[3:35]
        return None, None

    @staticmethod
    def _parse_memcached_value(uuid):
        value = MemcachedClient().get(key=uuid)
        if not value:
            return None, None, None, None
        value_list = value.split('&')
        if len(value_list) != 4:
            return None, None, None, None
        [md5_stamp, time_stamp, user_id, role_id] = value_list
        return int(user_id), int(role_id), md5_stamp, time_stamp


class Grant(object):
    def load_permission(self, role=None):
        if role:
            self.set_permission(role=role)
        else:
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
            except RolePermission.DoesNotExist:
                perm[v] = {'state': False}
        MemcachedClient().set('PERMISSION_' + str(role.id), json.dumps(perm))
        return perm


class LevelObject(object):
    def __init__(self, level=0):
        self.level = int(level)

    def __cmp__(self, other):
        if isinstance(other, (int, float)):
            value = other
        elif isinstance(other, LevelObject):
            value = other.level
        else:
            return -1
        if self.level < value:
            return -1
        elif self.level > value:
            return 1
        else:
            return 0

    def is_gt_lv10(self):
        return self.level >= PermissionLevel.LEVEL_10

    def is_gt_lv9(self):
        return self.level >= PermissionLevel.LEVEL_9

    def is_gt_lv8(self):
        return self.level >= PermissionLevel.LEVEL_8

    def is_gt_lv7(self):
        return self.level >= PermissionLevel.LEVEL_7

    def is_gt_lv6(self):
        return self.level >= PermissionLevel.LEVEL_6

    def is_gt_lv5(self):
        return self.level >= PermissionLevel.LEVEL_5

    def is_gt_lv4(self):
        return self.level >= PermissionLevel.LEVEL_4

    def is_gt_lv3(self):
        return self.level >= PermissionLevel.LEVEL_3

    def is_gt_lv2(self):
        return self.level >= PermissionLevel.LEVEL_2

    def is_gt_lv1(self):
        return self.level >= PermissionLevel.LEVEL_1

    def is_lt_lv10(self):
        return self.level < PermissionLevel.LEVEL_10

    def is_lt_lv9(self):
        return self.level < PermissionLevel.LEVEL_9

    def is_lt_lv8(self):
        return self.level < PermissionLevel.LEVEL_8

    def is_lt_lv7(self):
        return self.level < PermissionLevel.LEVEL_7

    def is_lt_lv6(self):
        return self.level < PermissionLevel.LEVEL_6

    def is_lt_lv5(self):
        return self.level < PermissionLevel.LEVEL_5

    def is_lt_lv4(self):
        return self.level < PermissionLevel.LEVEL_4

    def is_lt_lv3(self):
        return self.level < PermissionLevel.LEVEL_3

    def is_lt_lv2(self):
        return self.level < PermissionLevel.LEVEL_2

    def is_lt_lv1(self):
        return self.level < PermissionLevel.LEVEL_1


class Service(object):
    def __init__(self, request, instance=None, auth_type=AuthType.HEADER):
        if instance:
            self.request = instance.request
            self.token = instance.token
            self.uuid, self.uid, self.role_id = instance.uuid, instance.uid, instance.role_id
            self.permission = instance.permission
            self.role_level = instance.role_level
            return
        self.request = request
        self.token = request.META.get('HTTP_AUTH_TOKEN') \
            if auth_type == AuthType.HEADER else request.COOKIES.get('Auth-Token')
        self.uuid, self.uid, self.role_id = Authorize().auth_token(self.token)
        self.permission = Grant().get_permission(role_id=self.role_id)
        try:
            self.role_level = self.permission['_role_level']
        except KeyError:
            raise AuthError(code=503, message=ErrorMsg.PERMISSION_KEY_ERROR + '_role_level')

    def has_permission(self, perm_name, raise_error=True):
        if self._has_permission(perm_name):
            return True
        if raise_error:
            raise AuthError(code=403, message=ErrorMsg.PERMISSION_DENIED)
        return False

    def _has_permission(self, perm_name):
        try:
            if not self.permission[perm_name]['state']:
                return False
        except KeyError:
            return False
        return True

    def get_permission_level(self, perm_name, raise_error=True):
        if not self.has_permission(perm_name, raise_error):
            return LevelObject(0), LevelObject(0)
        try:
            major_level = LevelObject(self.permission[perm_name]['major_level'])
        except KeyError:
            major_level = LevelObject(0)
        try:
            minor_level = LevelObject(self.permission[perm_name]['minor_level'])
        except KeyError:
            minor_level = LevelObject(0)
        return major_level, minor_level

    def get_permission_value(self, perm_name, raise_error=True):
        if not self.has_permission(perm_name, raise_error):
            return 0
        try:
            return self.permission[perm_name]['value']
        except KeyError:
            return 0

    @staticmethod
    def choices_format(value, choices, default=None):
        if value in (None, ''):
            return default
        value = int(value)
        return value if value in dict(choices) else default

    @staticmethod
    def is_unique(model_obj, exclude_id=None, **kwargs):
        try:
            if model_obj.objects.exclude(id=exclude_id).get(**kwargs):
                raise ServiceError(message=ErrorMsg.DUPLICATE_IDENTITY)
        except model_obj.MultipleObjectsReturned:
            raise ServiceError(code=500, message=ErrorMsg.DUPLICATE_IDENTITY)
        except model_obj.DoesNotExist:
            return kwargs.values()[0]
