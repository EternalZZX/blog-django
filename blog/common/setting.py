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
    SIGN_UP = True
    SIGN_UP_KEY = False
    GUEST = True
    GUEST_ROLE = 3
    USER_CANCEL = True
    USERNAME_UPDATE = False
    NICK_UPDATE = True
    ARTICLE_CANCEL = True
    ARTICLE_AUDIT = True
    COMMENT_CANCEL = True
    COMMENT_AUDIT = True
    PHOTO_CANCEL = True
    PHOTO_AUDIT = True
    PHOTO_THUMBNAIL = True
    PHOTO_LARGE_SIZE = 2560
    PHOTO_MIDDLE_SIZE = 800
    PHOTO_SMALL_SIZE = 200
    HOT_EXPIRATION_TIME = 604800

    __instance = True

    def __init__(self):
        super(Setting, self).__init__()
        self._init_setting()

    @classmethod
    def load_setting(cls):
        settings = ServerSetting.objects.all()
        int_setting_keys = ['TOKEN_EXPIRATION_TIME', 'GUEST_ROLE',
                            'PHOTO_LARGE_SIZE', 'PHOTO_MIDDLE_SIZE',
                            'PHOTO_SMALL_SIZE', 'HOT_EXPIRATION_TIME']
        try:
            for k, v in SettingKey():
                value = cls._format_value(settings.get(key=v).value, 'int') \
                    if k in int_setting_keys else cls._format_value(settings.get(key=v).value)
                setattr(cls, k, value)
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
    SIGN_UP = 'sign_up'
    SIGN_UP_KEY = 'sign_up_key'
    GUEST = 'guest'
    GUEST_ROLE = 'guest_role'
    USER_CANCEL = 'user_cancel'
    USERNAME_UPDATE = 'username_update'
    NICK_UPDATE = 'nick_update'
    ARTICLE_CANCEL = 'article_cancel'
    ARTICLE_AUDIT = 'article_audit'
    COMMENT_CANCEL = 'comment_cancel'
    COMMENT_AUDIT = 'comment_audit'
    PHOTO_CANCEL = 'photo_cancel'
    PHOTO_AUDIT = 'photo_audit'
    PHOTO_THUMBNAIL = 'photo_thumbnail'
    PHOTO_LARGE_SIZE = 'photo_large_size'
    PHOTO_MIDDLE_SIZE = 'photo_middle_size'
    PHOTO_SMALL_SIZE = 'photo_small_size'
    HOT_EXPIRATION_TIME = 'hot_expiration_time'


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
    ARTICLE_LIKE = 'article_like'

    ALBUM_CREATE = 'album_create'
    ALBUM_DELETE = 'album_delete'
    ALBUM_UPDATE = 'album_update'
    ALBUM_SELECT = 'album_select'
    ALBUM_PRIVACY = 'album_privacy'
    ALBUM_SYSTEM = 'album_system'
    ALBUM_LIKE = 'album_like'

    PHOTO_CREATE = 'photo_create'
    PHOTO_DELETE = 'photo_delete'
    PHOTO_UPDATE = 'photo_update'
    PHOTO_SELECT = 'photo_select'
    PHOTO_PERMISSION = 'photo_permission'
    PHOTO_AUDIT = 'photo_audit'
    PHOTO_CANCEL = 'photo_cancel'
    PHOTO_PRIVACY = 'photo_privacy'
    PHOTO_READ = 'photo_read'
    PHOTO_LIMIT = 'photo_limit'
    PHOTO_LIKE = 'photo_like'

    COMMENT_CREATE = 'comment_create'
    COMMENT_DELETE = 'comment_delete'
    COMMENT_UPDATE = 'comment_update'
    COMMENT_SELECT = 'comment_select'
    COMMENT_PERMISSION = 'comment_permission'
    COMMENT_AUDIT = 'comment_audit'
    COMMENT_CANCEL = 'comment_cancel'
    COMMENT_LIKE = 'comment_like'

    MARK_CREATE = 'mark_create'
    MARK_DELETE = 'mark_delete'
    MARK_UPDATE = 'mark_update'
    MARK_SELECT = 'mark_select'
    MARK_PRIVACY = 'mark_privacy'


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


class AuthType(StaticObject):
    NONE = 0
    HEADER = 1
    COOKIE = 2
    URL = 3
