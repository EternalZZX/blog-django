#!/usr/bin/env python
# -*- coding: utf-8 -*-

from blog.account.models import ServerSetting
from blog.common.utils import StaticObject


class Setting(StaticObject):
    SESSION_LIMIT = True
    TOKEN_EXPIRATION = True
    TOKEN_EXPIRATION_TIME = 604800
    SIGN_UP_POLICY = True
    SIGN_UP_KEY = False
    NICK_UPDATE = True

    __instance = True

    def __init__(self):
        super(Setting, self).__init__()
        self._init_setting()

    @classmethod
    def load_setting(cls):
        settings = ServerSetting.objects.all()
        cls.SESSION_LIMIT = cls._format_value(settings.get(key=SettingKey.SESSION_LIMIT).value)
        cls.TOKEN_EXPIRATION = cls._format_value(settings.get(key=SettingKey.TOKEN_EXPIRATION).value)
        cls.TOKEN_EXPIRATION_TIME = cls._format_value(settings.get(key=SettingKey.TOKEN_EXPIRATION_TIME).value, 'int')
        cls.SIGN_UP_POLICY = cls._format_value(settings.get(key=SettingKey.SIGN_UP_POLICY).value)
        cls.SIGN_UP_KEY = cls._format_value(settings.get(key=SettingKey.SIGN_UP_KEY).value)
        cls.NICK_UPDATE = cls._format_value(settings.get(key=SettingKey.NICK_UPDATE).value)

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
    NICK_UPDATE = 'nick_update'


class PermissionName(StaticObject):
    LOGIN = 'login'
    STEALTH = 'stealth'
    SEARCH = 'search'
    CUSTOM_TITLE = 'custom_title'

    READ = 'read'
    REPORT = 'report'
    REPLY = 'reply'
    APPRAISE = 'appraise'
    MESSAGE = 'message'

    OPERATE = 'operate'

    USER_CREATE = 'user_create'
    USER_DELETE = 'user_delete'
    USER_UPDATE = 'user_update'
    USER_SELECT = 'user_select'


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
