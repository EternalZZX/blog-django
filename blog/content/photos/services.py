#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid
import time

from functools import reduce

from django.db.models import Q
from django.utils.timezone import now, timedelta
from django.core.files.images import ImageFile

from blog.content.photos.models import Photo
from blog.common.base import Service
from blog.common.error import ServiceError
from blog.common.message import ErrorMsg, ContentErrorMsg
from blog.common.utils import paging, model_to_dict, html_to_str
from blog.common.setting import Setting, PermissionName


class PhotoService(Service):
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
