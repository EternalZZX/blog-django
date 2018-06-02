#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import requests

from poster.encode import multipart_encode
from poster.streaminghttp import register_openers

from blog.settings import MEDIA_ROOT, MEDIA_URL
from blog.wechat.common.base import AccessService


class Media(object):
    def __init__(self):
        register_openers()

    def photo_upload(self, url):
        image_path = os.path.join(MEDIA_ROOT, url.replace(MEDIA_URL, ''))
        image_data = open(image_path, "rb").read()
        post_url = "https://api.weixin.qq.com/cgi-bin/media/upload?" \
                   "access_token=%s&type=image" % AccessService.get_access_token()
        data, headers = multipart_encode({'media': image_data})
        response = requests.post(post_url, files=data, headers=headers)
        return json.loads(response.content)['mediaId']
