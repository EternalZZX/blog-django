#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import urllib2

from poster.encode import multipart_encode
from poster.streaminghttp import register_openers

from blog.wechat.common.base import AccessService
from blog.common.error import ServiceError
from blog.settings import MEDIA_ROOT, MEDIA_URL


class MediaService(object):
    base_url = "https://api.weixin.qq.com/cgi-bin/media"
    upload_url = "%s/upload" % base_url
    download_url = "%s/get" % base_url

    def __init__(self):
        self.token = AccessService.get_access_token()
        register_openers()

    def photo_upload(self, photo_url):
        image_path = os.path.join(MEDIA_ROOT, photo_url.replace(MEDIA_URL, ''))
        image_data = open(image_path, "rb")
        post_url = "%s?access_token=%s&type=image" % (self.upload_url, self.token)
        post_data, post_headers = multipart_encode({'media': image_data})
        request = urllib2.Request(post_url, post_data, post_headers)
        response = urllib2.urlopen(request)
        response = json.loads(response.read())
        try:
            media_id = response['media_id']
        except KeyError:
            raise ServiceError(code=response['errcode'], message=response['errmsg'])
        return media_id

    def photo_download(self, media_id):
        postUrl = "%s?access_token=%s&media_id=%s" % (self.download_url, self.token, media_id)
        response = urllib2.urlopen(postUrl)
        headers = response.info().__dict__['headers']
        if ('Content-Type: application/json\r\n' in headers) or ('Content-Type: text/plain\r\n' in headers):
            response = json.loads(response.read())
            raise ServiceError(code=response['errcode'], message=response['errmsg'])
        return response.read()
