#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid
import time

from django.db.models import Q

from blog.account.users.models import User
from blog.account.users.services import UserService
from blog.content.albums.models import Album
from blog.common.base import Service
from blog.common.error import ServiceError
from blog.common.message import ErrorMsg, AccountErrorMsg, ContentErrorMsg
from blog.common.utils import paging, model_to_dict
from blog.common.setting import PermissionName


class AlbumService(Service):
    def create(self, name, description=None, author_uuid=None, privacy=Album.PUBLIC):
        create_level, _ = self.get_permission_level(PermissionName.ALBUM_CREATE)
        album_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, (name + self.uuid + str(time.time())).encode('utf-8')))
        author_id = self.uid
        if author_uuid and create_level.is_gt_lv10():
            try:
                author_id = User.objects.get(uuid=author_uuid).id
            except User.DoesNotExist:
                raise ServiceError(message=AccountErrorMsg.USER_NOT_FOUND)
        privacy = self._get_privacy(privacy=privacy)
        album = Album.objects.create(uuid=album_uuid,
                                     name=name,
                                     description=description,
                                     author_id=author_id,
                                     privacy=privacy)
        album_dict = AlbumService._album_to_dict(album=album)
        return 201, album_dict

    def _get_privacy(self, privacy=Album.PUBLIC):
        _, privacy_level = self.get_permission_level(PermissionName.ALBUM_PRIVACY, False)
        privacy = AlbumService.choices_format(privacy, Album.PRIVACY_CHOICES, Album.PUBLIC)
        if privacy == Album.PROTECTED and privacy_level.is_lt_lv1() or \
                privacy == Album.PRIVATE and privacy_level.is_lt_lv2():
            privacy = Album.PUBLIC
        return privacy

    @staticmethod
    def _album_to_dict(album, **kwargs):
        album_dict = model_to_dict(album)
        author_dict = model_to_dict(album.author)
        album_dict['author'] = {}
        for field in UserService.USER_PUBLIC_FIELD:
            album_dict['author'][field] = author_dict[field]
        for key in kwargs:
            album_dict[key] = kwargs[key]
        return album_dict
