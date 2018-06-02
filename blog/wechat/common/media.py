#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import requests

from blog.settings import MEDIA_ROOT, MEDIA_URL
from blog.wechat.common.base import AccessService


class Media(object):
    @staticmethod
    def photo_upload(url):
        image_path = os.path.join(MEDIA_ROOT, url.replace(MEDIA_URL, ''))
        image_data = open(image_path, "rb").read()
        post_url = "https://api.weixin.qq.com/cgi-bin/media/upload?" \
                   "access_token=%s&type=image" % AccessService.get_access_token()
        response = requests.post(post_url,
                                 files={
                                     'media': image_data
                                 })
        return json.loads(response.content)['mediaId']
