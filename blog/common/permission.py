#!/usr/bin/env python
# -*- coding: utf-8 -*-


class PermissionName(object):
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

    def __init__(self):
        pass

    @classmethod
    def __iter__(cls):
        properties = filter(lambda item: item[0][:2] != '__', cls.__dict__.items())
        return iter(properties)

