#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import redis
import memcache
import random
import time
import json

from functools import reduce
from abc import ABCMeta, abstractmethod

from django.db.models import Q

from blog.account.users.models import User
from blog.account.roles.models import Role, RolePermission
from blog.common.error import AuthError, ServiceError
from blog.common.message import ErrorMsg, AccountErrorMsg
from blog.common.setting import Setting, PermissionName, PermissionLevel, AuthType
from blog.common.utils import ignored, get_md5
from blog.settings import REDIS_HOSTS, REDIS_PASSWORD, MEMCACHED_HOSTS


class RedisClient(object):
    __pool = None

    def __init__(self):
        if not self.__pool:
            self._init_pool()
        self.client = redis.StrictRedis(connection_pool=self.__pool)

    @classmethod
    def _init_pool(cls):
        cls.__pool = redis.ConnectionPool(host=REDIS_HOSTS, port=6379,
                                          db=0, password=REDIS_PASSWORD)

    def set(self, name, value, ex=None):
        return self.client.set(name, value, ex)

    def get(self, name):
        return self.client.get(name)

    def exists(self, name):
        return self.client.exists(name)

    def delete(self, *names):
        return self.client.delete(*names)

    def set_add(self, name, *values):
        return self.client.sadd(name, *values)

    def set_all(self, name):
        return self.client.smembers(name)

    def set_count(self, name):
        return self.client.scard(name)

    def set_delete(self, name, *values):
        return self.client.srem(name, *values)

    def hash_set(self, name, key, value):
        return self.client.hset(name, key, value)

    def hash_get(self, name, key):
        return self.client.hget(name, key)

    def hash_delete(self, name, *keys):
        return self.client.hdel(name, *keys)

    def hash_increase(self, name, key, amount=1):
        return self.client.hincrby(name, key, amount)

    def hash_all(self, name):
        return self.client.hgetall(name)

    def hash_keys(self, name):
        return self.client.hkeys(name)

    def sorted_set_add(self, name, *args, **kwargs):
        return self.client.zadd(name, *args, **kwargs)

    def sorted_set_range(self, name, start=0, end=-1, desc=True,
                         withscores=False, score_cast_func=int):
        return self.client.zrange(name, start, end, desc,
                                  withscores, score_cast_func)

    def sorted_set_count(self, name):
        return self.client.zcard(name)

    def sorted_set_delete(self, name, *values):
        return self.client.zrem(name, *values)


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
        if not Setting().SESSION_LIMIT and RedisClient().get(name=uuid):
            token = self.update_token(uuid=uuid)
        else:
            md5 = get_md5(str(random.random()))
            token = base64.b64encode('ETE%s%s' % (md5, base64.b64encode(uuid))).rstrip('=')
            self._save_token(uuid=uuid, md5=md5)
        return token

    def update_token(self, token=None, uuid=None, role_id=None):
        if uuid and RedisClient().get(name=uuid):
            user_id, role_id_stamp, md5_stamp, time_stamp = self._parse_memcached_value(uuid=uuid)
            token = base64.b64encode('ETE%s%s' % (md5_stamp, base64.b64encode(uuid))).rstrip('=')
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
        if not token:
            raise AuthError()
        uuid, user_id, role_id, md5_stamp, time_stamp = self._auth_token_md5(token=token)
        if Setting().TOKEN_EXPIRATION and time.time() - int(time_stamp) > Setting().TOKEN_EXPIRATION_TIME:
            RedisClient().delete(uuid)
            raise AuthError(code=419, message=AccountErrorMsg.TOKEN_TIMEOUT)
        self._save_token(uuid=uuid, md5=md5_stamp, user_id=user_id, role_id=role_id)
        return uuid, user_id, role_id

    @staticmethod
    def cancel_token(uuid):
        RedisClient().delete(uuid)

    def _auth_token_md5(self, token):
        uuid, md5 = self._parse_token(token=token)
        if not uuid:
            raise AuthError()
        user_id, role_id, md5_stamp, time_stamp = self._parse_memcached_value(uuid=uuid)
        if not md5_stamp:
            raise AuthError(code=419, message=AccountErrorMsg.TOKEN_TIMEOUT)
        if md5_stamp != md5:
            raise AuthError(code=418, message=AccountErrorMsg.UNEXPECTED_FLAG)
        return uuid, user_id, role_id, md5_stamp, time_stamp

    @staticmethod
    def _save_token(uuid, md5, time_stamp=None, user_id=None, role_id=None):
        if not time_stamp:
            time_stamp = str(int(time.time()))
        if not user_id or not role_id:
            try:
                user = User.objects.get(uuid=uuid)
                user_id = user.id
                role_id = user.role.id
            except User.DoesNotExist:
                raise AuthError()
        if not user_id or not role_id:
            raise AuthError()
        value = '%s&%s&%s&%s' % (md5, time_stamp, user_id, role_id)
        RedisClient().set(name=uuid, value=value, ex=Setting().TOKEN_EXPIRATION_TIME)

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
        value = RedisClient().get(name=uuid)
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
        value = RedisClient().hash_get(name='ROLE_PERMISSION', key=str(role_id))
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
        RedisClient().hash_set(name='ROLE_PERMISSION', key=str(role.id), value=json.dumps(perm))
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
        self.auth_type = auth_type
        self.token = None
        self.uuid, self.uid, self.role_id = None, None, None
        self.permission = None
        self.role_level = None
        if auth_type != AuthType.NONE:
            self._auth_init()

    def _auth_init(self):
        if self.auth_type == AuthType.HEADER:
            self.token = self.request.META.get('HTTP_AUTH_TOKEN')
        elif self.auth_type == AuthType.COOKIE:
            self.token = self.request.COOKIES.get('Auth-Token')
        self.uuid, self.uid, self.role_id = Authorize().auth_token(self.token)
        self.permission = Grant().get_permission(role_id=self.role_id)
        try:
            self.role_level = self.permission['_role_level']
        except (KeyError, TypeError):
            raise AuthError(code=503, message=ErrorMsg.PERMISSION_KEY_ERROR + '_role_level')

    def has_permission(self, perm_name, raise_error=True):
        if self.auth_type == AuthType.NONE:
            return True
        if self._has_permission(perm_name):
            return True
        if raise_error:
            raise AuthError(code=403, message=ErrorMsg.PERMISSION_DENIED)
        return False

    def _has_permission(self, perm_name):
        try:
            if not self.permission[perm_name]['state']:
                return False
        except (KeyError, TypeError):
            return False
        return True

    def get_permission_level(self, perm_name, raise_error=True):
        if not self.has_permission(perm_name, raise_error):
            return LevelObject(0), LevelObject(0)
        try:
            major_level = LevelObject(self.permission[perm_name]['major_level'])
        except (KeyError, TypeError):
            major_level = LevelObject(0)
        try:
            minor_level = LevelObject(self.permission[perm_name]['minor_level'])
        except (KeyError, TypeError):
            minor_level = LevelObject(0)
        return major_level, minor_level

    def get_permission_value(self, perm_name, raise_error=True):
        if not self.has_permission(perm_name, raise_error):
            return 0
        try:
            return self.permission[perm_name]['value']
        except (KeyError, TypeError):
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
                raise ServiceError(code=409, message=ErrorMsg.DUPLICATE_IDENTITY)
        except model_obj.MultipleObjectsReturned:
            raise ServiceError(code=500, message=ErrorMsg.DUPLICATE_IDENTITY)
        except model_obj.DoesNotExist:
            return kwargs.values()[0]

    @staticmethod
    def status_or(a, b):
        return (a if isinstance(a, Q) else Q(status=int(a))) | Q(status=int(b))

    @staticmethod
    def query_by_list(objects, query_list):
        query_option = reduce(Service._query_or, query_list)
        if isinstance(query_option, dict):
            return objects.filter(**query_option)
        return objects.filter(query_option)

    @staticmethod
    def _query_or(a, b):
        return (a if isinstance(a, Q) else Q(**a)) | Q(**b)


class MetadataService(object):
    METADATA_KEY = 'RESOURCE_METADATA'
    LIKE_LIST_KEY = 'RESOURCE_LIKE_LIST'
    DISLIKE_LIST_KEY = 'RESOURCE_DISLIKE_LIST'

    OPERATE_ADD = 1
    OPERATE_MINUS = 0
    OPERATE_LIKE = 1
    OPERATE_DISLIKE = 0

    LIKE_LIST = 1
    DISLIKE_LIST = 2
    ALL_LIST = 3

    NONE_USER = 0
    LIKE_USER = 1
    DISLIKE_USER = 2

    __metaclass__ = ABCMeta

    def __init__(self):
        self.redis_client = RedisClient()

    class Metadata:
        def __init__(self, *args):
            self.read_count = int(args[0])
            self.comment_count = int(args[1])
            self.like_count = int(args[2])
            self.dislike_count = int(args[3])
            self.time_stamp = int(args[4])

    def get_metadata(self, resource, start=0, end=-1, list_type=LIKE_LIST):
        metadata = self.get_metadata_count(resource=resource)
        like_users, dislike_users = self._get_like_list(resource, start, end, list_type)
        return metadata, like_users, dislike_users

    def get_metadata_count(self, resource):
        metadata = self._get_metadata_count(resource=resource)
        metadata.time_stamp = int(time.time())
        self._set_redis_metadata_count(resource=resource, metadata=metadata)
        return metadata

    def update_metadata_count(self, resource, **kwargs):
        metadata = self._get_metadata_count(resource=resource)
        for field in kwargs:
            count = getattr(metadata, field)
            count = count + 1 if int(kwargs[field]) == self.OPERATE_ADD else count - 1
            setattr(metadata, field, count)
        metadata.time_stamp = int(time.time())
        self._set_redis_metadata_count(resource=resource, metadata=metadata)
        return metadata

    def update_like_list(self, resource, user_id, operate=OPERATE_LIKE):
        user_id = str(user_id)
        like_list_key, dislike_list_key = self._get_like_list_key(resource.uuid)
        time_stamp = int(time.time())
        operate_dict = {}
        like_users, dislike_users = self._get_like_list(resource=resource, list_type=self.ALL_LIST)
        if int(operate) == self.OPERATE_LIKE:
            if user_id in dislike_users:
                self.redis_client.sorted_set_delete(dislike_list_key, user_id)
                operate_dict['dislike_count'] = self.OPERATE_MINUS
            if user_id not in like_users:
                self.redis_client.sorted_set_add(like_list_key, time_stamp, user_id)
                operate_dict['like_count'] = self.OPERATE_ADD
            else:
                self.redis_client.sorted_set_delete(like_list_key, user_id)
                operate_dict['like_count'] = self.OPERATE_MINUS
        elif int(operate) == self.OPERATE_DISLIKE:
            if user_id in like_users:
                self.redis_client.sorted_set_delete(like_list_key, user_id)
                operate_dict['like_count'] = self.OPERATE_MINUS
            if user_id not in dislike_users:
                self.redis_client.sorted_set_add(dislike_list_key, time_stamp, user_id)
                operate_dict['dislike_count'] = self.OPERATE_ADD
            else:
                self.redis_client.sorted_set_delete(dislike_list_key, user_id)
                operate_dict['dislike_count'] = self.OPERATE_MINUS
        return self.update_metadata_count(resource=resource, **operate_dict)

    def sync_metadata(self):
        metadata_dict = self.redis_client.hash_all(name=self.METADATA_KEY)
        for resource_uuid, value in metadata_dict.items():
            value_list = value.split('&')
            if len(value_list) != 5:
                self.redis_client.hash_delete(self.METADATA_KEY, resource_uuid)
                like_list_key, dislike_list_key = self._get_like_list_key(resource_uuid)
                self.redis_client.delete(like_list_key, dislike_list_key)
                continue
            metadata = self.Metadata(*value_list)
            self._set_sql_metadata(resource_uuid=resource_uuid, metadata=metadata)

    def is_like_user(self, resource, user_id):
        like_users, _ = self._get_like_list(resource=resource, list_type=self.LIKE_LIST)
        if str(user_id) in like_users:
            return self.LIKE_USER
        _, dislike_users = self._get_like_list(resource=resource, list_type=self.DISLIKE_LIST)
        if str(user_id) in dislike_users:
            return self.DISLIKE_USER
        return self.NONE_USER

    def _get_metadata_count(self, resource):
        value = self.redis_client.hash_get(name=self.METADATA_KEY, key=resource.uuid)
        if not value:
            return self._get_sql_metadata_count(resource=resource)
        value_list = value.split('&')
        if len(value_list) != 5:
            return self._get_sql_metadata_count(resource=resource)
        return self.Metadata(*value_list)

    def _get_like_list(self, resource, start=0, end=-1, list_type=LIKE_LIST):
        start = 0 if start is None else int(start)
        end = -1 if end is None or int(end) == -1 else int(end) + 1
        list_type, like_users, dislike_users = int(list_type), None, None
        like_list_key, dislike_list_key = self._get_like_list_key(resource.uuid)
        if list_type in (self.LIKE_LIST, self.ALL_LIST):
            like_users = self.redis_client.sorted_set_range(like_list_key, start, end)
            if not like_users:
                return self._get_sql_like_list(resource=resource)
            like_users.remove('PLACEHOLDER')
        if list_type in (self.DISLIKE_LIST, self.ALL_LIST):
            dislike_users = self.redis_client.sorted_set_range(dislike_list_key, start, end)
            if not dislike_users:
                return self._get_sql_like_list(resource=resource)
            dislike_users.remove('PLACEHOLDER')
        return like_users, dislike_users

    def _set_redis_metadata_count(self, resource, metadata):
        value = '%s&%s&%s&%s&%s' % (metadata.read_count, metadata.comment_count,
                                    metadata.like_count, metadata.dislike_count,
                                    metadata.time_stamp)
        self.redis_client.hash_set(name=self.METADATA_KEY, key=resource.uuid, value=value)

    def _set_redis_like_list(self, resource, like_users, dislike_users):
        like_list_key, dislike_list_key = self._get_like_list_key(resource.uuid)
        time_stamp = int(time.time())
        self.redis_client.delete(like_list_key, dislike_list_key)
        self.redis_client.sorted_set_add(like_list_key, time_stamp, 'PLACEHOLDER')
        self.redis_client.sorted_set_add(dislike_list_key, time_stamp, 'PLACEHOLDER')
        for user_uid in like_users:
            self.redis_client.sorted_set_add(like_list_key, time_stamp, user_uid)
        for user_uid in dislike_users:
            self.redis_client.sorted_set_add(dislike_list_key, time_stamp, user_uid)

    def _get_sql_metadata_count(self, resource):
        read_count = resource.metadata.read_count
        comment_count = resource.metadata.comment_count
        like_count = resource.metadata.like_count
        dislike_count = resource.metadata.dislike_count
        time_stamp = str(int(time.time()))
        metadata = self.Metadata(read_count, comment_count, like_count, dislike_count, time_stamp)
        self._set_redis_metadata_count(resource=resource, metadata=metadata)
        return metadata

    def _get_sql_like_list(self, resource):
        like_users = resource.metadata.like_users.all()
        like_users = list(user.id for user in like_users)
        dislike_users = resource.metadata.dislike_users.all()
        dislike_users = list(user.id for user in dislike_users)
        self._set_redis_like_list(resource=resource,
                                  like_users=like_users,
                                  dislike_users=dislike_users)
        return like_users, dislike_users

    @abstractmethod
    def _set_sql_metadata(self, resource_uuid, metadata):
        pass

    def _set_resource_sql_metadata(self, resource, metadata, like_list_key, dislike_list_key):
        resource.metadata.read_count = metadata.read_count
        resource.metadata.comment_count = metadata.comment_count
        resource.metadata.like_count = metadata.like_count
        resource.metadata.dislike_count = metadata.dislike_count
        if self.redis_client.exists(name=like_list_key):
            like_users, dislike_users = self._get_like_list(resource=resource, list_type=self.ALL_LIST)
            resource.metadata.like_users.clear()
            for user_uid in like_users:
                with ignored(User.DoesNotExist):
                    resource.metadata.like_users.add(user_uid)
            resource.metadata.dislike_users.clear()
            for user_uid in dislike_users:
                with ignored(User.DoesNotExist):
                    resource.metadata.dislike_users.add(user_uid)
        resource.metadata.save()
        if time.time() - metadata.time_stamp > Setting().HOT_EXPIRATION_TIME:
            self.redis_client.hash_delete(self.METADATA_KEY, resource.uuid)
            self.redis_client.delete(like_list_key, dislike_list_key)

    def _get_like_list_key(self, resource_uuid):
        like_list_key = '%s&%s' % (self.LIKE_LIST_KEY, resource_uuid)
        dislike_list_key = '%s&%s' % (self.DISLIKE_LIST_KEY, resource_uuid)
        return like_list_key, dislike_list_key
