#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import json

from blog.common.error import ServiceError
from blog.settings import APP_ID, APP_SECRET


class AccessService(object):
    base_url = "https://api.weixin.qq.com/cgi-bin"
    token_url = "%s/token" % base_url
    __accessToken = ''

    @classmethod
    def get_access_token(cls):
        if not cls.__accessToken:
            return cls.update_access_token()
        return cls.__accessToken

    @classmethod
    def update_access_token(cls):
        url = ("%s?grant_type=client_credential&appid=%s&secret=%s" % (cls.token_url, APP_ID, APP_SECRET))
        response = urllib.urlopen(url)
        response = json.loads(response.read())
        try:
            cls.__accessToken = response['access_token']
        except KeyError:
            raise ServiceError(code=response['errcode'], message=response['errmsg'])
        return cls.__accessToken
