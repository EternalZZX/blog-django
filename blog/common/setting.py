#!/usr/bin/env python
# -*- coding: utf-8 -*-

from blog.account.models import ServerSetting
from blog.common.utils import StaticObject
from blog.common.error import ServerError
from blog.common.message import ErrorMsg


class Setting(StaticObject):
    SESSION_LIMIT = True
    TOKEN_EXPIRATION = True
    TOKEN_EXPIRATION_TIME = 604800
    SIGN_UP_POLICY = True
    SIGN_UP_KEY = False
    USER_CANCEL = True
    USERNAME_UPDATE = False
    NICK_UPDATE = True
    ARTICLE_CANCEL = True
    ARTICLE_AUDIT = False

    __instance = True

    def __init__(self):
        super(Setting, self).__init__()
        self._init_setting()

    @classmethod
    def load_setting(cls):
        settings = ServerSetting.objects.all()
        try:
            cls.SESSION_LIMIT = cls._format_value(settings.get(key=SettingKey.SESSION_LIMIT).value)
            cls.TOKEN_EXPIRATION = cls._format_value(settings.get(key=SettingKey.TOKEN_EXPIRATION).value)
            cls.TOKEN_EXPIRATION_TIME = cls._format_value(settings.get(key=SettingKey.TOKEN_EXPIRATION_TIME).value,
                                                          'int')
            cls.SIGN_UP_POLICY = cls._format_value(settings.get(key=SettingKey.SIGN_UP_POLICY).value)
            cls.SIGN_UP_KEY = cls._format_value(settings.get(key=SettingKey.SIGN_UP_KEY).value)
            cls.USER_CANCEL = cls._format_value(settings.get(key=SettingKey.USER_CANCEL).value)
            cls.USERNAME_UPDATE = cls._format_value(settings.get(key=SettingKey.USERNAME_UPDATE).value)
            cls.NICK_UPDATE = cls._format_value(settings.get(key=SettingKey.NICK_UPDATE).value)
            cls.ARTICLE_CANCEL = cls._format_value(settings.get(key=SettingKey.ARTICLE_CANCEL).value)
            cls.ARTICLE_AUDIT = cls._format_value(settings.get(key=SettingKey.ARTICLE_AUDIT).value)
        except ServerSetting.DoesNotExist:
            raise ServerError(code=503, message=ErrorMsg.SETTING_ERROR)

    @classmethod
    def _init_setting(cls):
        if cls.__instance:
            cls.load_setting()
            cls.__instance = False

    @classmethod
    def _format_value(cls, value, date_type='bool'):
        if date_type == 'bool':
            return value == 'on'
        elif date_type == 'int':
            return int(value)
        else:
            return value


class SettingKey(StaticObject):
    SESSION_LIMIT = 'session_limit'
    TOKEN_EXPIRATION = 'token_expiration'
    TOKEN_EXPIRATION_TIME = 'token_expiration_time'
    SIGN_UP_POLICY = 'sign_up_policy'
    SIGN_UP_KEY = 'sign_up_key'
    USER_CANCEL = 'user_cancel'
    USERNAME_UPDATE = 'username_update'
    NICK_UPDATE = 'nick_update'
    ARTICLE_CANCEL = 'article_cancel'
    ARTICLE_AUDIT = 'article_audit'


class PermissionName(StaticObject):
    LOGIN = 'login'
    READ_LEVEL = 'read_level'

    USER_CREATE = 'user_create'
    USER_DELETE = 'user_delete'
    USER_UPDATE = 'user_update'
    USER_SELECT = 'user_select'
    USER_PRIVACY = 'user_privacy'
    USER_ROLE = 'user_role'
    USER_STATUS = 'user_status'
    USER_CANCEL = 'user_cancel'

    ROLE_CREATE = 'role_create'
    ROLE_DELETE = 'role_delete'
    ROLE_UPDATE = 'role_update'
    ROLE_SELECT = 'role_select'

    SECTION_CREATE = 'section_create'
    SECTION_DELETE = 'section_delete'
    SECTION_UPDATE = 'section_update'
    SECTION_SELECT = 'section_select'
    SECTION_PERMISSION = 'section_permission'

    ARTICLE_CREATE = 'article_create'
    ARTICLE_DELETE = 'article_delete'
    ARTICLE_UPDATE = 'article_update'
    ARTICLE_SELECT = 'article_select'
    ARTICLE_PERMISSION = 'article_permission'
    ARTICLE_AUDIT = 'article_audit'
    ARTICLE_CANCEL = 'article_cancel'
    ARTICLE_PRIVACY = 'article_privacy'
    ARTICLE_READ = 'article_read'


class PermissionLevel(StaticObject):
    LEVEL_10 = 1000
    LEVEL_9 = 900
    LEVEL_8 = 800
    LEVEL_7 = 700
    LEVEL_6 = 600
    LEVEL_5 = 500
    LEVEL_4 = 400
    LEVEL_3 = 300
    LEVEL_2 = 200
    LEVEL_1 = 100
    LEVEL_0 = 0
