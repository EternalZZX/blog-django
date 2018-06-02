#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import json

from blog.settings import APP_ID, APP_SECRET


class AccessService(object):
    __accessToken = ''

    @classmethod
    def get_access_token(cls):
        if not cls.__accessToken:
            return cls.update_access_token()
        return cls.__accessToken

    @classmethod
    def update_access_token(cls):
        url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type="
               "client_credential&appid=%s&secret=%s" % (APP_ID, APP_SECRET))
        response = urllib.urlopen(url)
        response = json.loads(response.read())
        cls._accessToken = response['access_token']
        return cls.__accessToken
