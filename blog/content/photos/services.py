#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid
import time
import os

from functools import reduce

from django.db.models import Q
from django.utils.timezone import now, timedelta
from django.core.files.images import ImageFile

from blog.settings import MEDIA_ROOT, MEDIA_URL
from blog.content.photos.models import Photo
from blog.common.base import Service
from blog.common.error import ServiceError
from blog.common.message import ErrorMsg, ContentErrorMsg
from blog.common.utils import paging, model_to_dict, html_to_str
from blog.common.setting import Setting, PermissionName


class PhotoService(Service):
    def show(self, url):
        image_path = os.path.join(MEDIA_ROOT, url.replace(MEDIA_URL, ''))
        image_data = open(image_path, "rb").read()
        return 200, image_data

    def get(self, photo_uuid):
        # self.has_permission(PermissionName.ARTICLE_SELECT)
        try:
            photo = Photo.objects.get(uuid=photo_uuid)
            # get_permission, read_permission = self._has_get_permission(article=article)
            # if not get_permission:
            #     raise Article.DoesNotExist
            # article_dict = ArticleService._article_to_dict(article=article)
        except Photo.DoesNotExist:
            raise ServiceError(code=404,
                               message=ContentErrorMsg.PHOTO_NOT_FOUND)
        return 200, model_to_dict(photo)

    def create(self, image, description=None, status=Photo.AUDIT,
               privacy=Photo.PUBLIC, read_level=100):
        # self.has_permission(PermissionName.ARTICLE_CREATE)
        photo_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, (description + self.uuid + str(time.time())).encode('utf-8')))
        # image = ImageFile(image)
        # status = self._get_create_status(status=status, section=section)
        # privacy = self._get_privacy(privacy=privacy)
        # read_level = self._get_read_level(read_level=read_level)
        photo = Photo.objects.create(uuid=photo_uuid,
                                     image=image,
                                     description=description,
                                     author_id=self.uid,
                                     status=status,
                                     privacy=privacy,
                                     read_level=read_level)
        return 201, model_to_dict(photo)
