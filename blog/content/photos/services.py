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
from blog.account.users.services import UserService
from blog.content.albums.models import Album
from blog.content.albums.services import AlbumService
from blog.content.photos.models import Photo
from blog.common.base import Service
from blog.common.error import ServiceError
from blog.common.message import ErrorMsg, ContentErrorMsg
from blog.common.utils import paging, model_to_dict, html_to_str
from blog.common.setting import Setting, PermissionName


class PhotoService(Service):
    def __init__(self, request):
        super(PhotoService, self).__init__(request=request)
        self.album_service = AlbumService(request=request, instance=self)

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

    def create(self, image, description=None, album_uuid=None,
               status=Photo.AUDIT, privacy=Photo.PUBLIC, read_level=100):
        self.has_permission(PermissionName.PHOTO_CREATE)
        photo_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, (description + self.uuid + str(time.time())).encode('utf-8')))
        # image = ImageFile(image)
        album = self._get_album(album_uuid=album_uuid)
        status = self._get_create_status(status=status, album=album)
        privacy = self._get_privacy(privacy=privacy)
        read_level = self._get_read_level(read_level=read_level)
        photo = Photo.objects.create(uuid=photo_uuid,
                                     image=image,
                                     description=description,
                                     author_id=self.uid,
                                     album=album,
                                     status=status,
                                     privacy=privacy,
                                     read_level=read_level)
        return 201, PhotoService._photo_to_dict(photo=photo)

    def _get_album(self, album_uuid):
        album = None
        if album_uuid:
            try:
                album = Album.objects.get(uuid=album_uuid)
                if album.author_id != self.uid:
                    update_level, _ = self.get_permission_level(PermissionName.ALBUM_UPDATE)
                    if update_level.is_lt_lv10():
                        raise Album.DoesNotExist
            except Album.DoesNotExist:
                raise ServiceError(code=400, message=ContentErrorMsg.ALBUM_NOT_FOUND)
        return album

    def _get_create_status(self, status, album):
        default = Photo.AUDIT if Setting().ARTICLE_AUDIT else Photo.ACTIVE
        status = PhotoService.choices_format(status, Photo.STATUS_CHOICES, default)
        if status == Photo.AUDIT:
            return default if album else Photo.ACTIVE
        if status == Photo.ACTIVE or status == Photo.FAILED:
            if album and Setting().ARTICLE_AUDIT:
                _, audit_level = self.get_permission_level(PermissionName.PHOTO_AUDIT, False)
                if audit_level.is_gt_lv10():
                    return status
                raise ServiceError(code=403, message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
            elif status == Photo.ACTIVE:
                return Photo.ACTIVE
            raise ServiceError(code=403, message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
        if status == Photo.CANCEL:
            if album and Setting().PHOTO_CANCEL:
                _, cancel_level = self.get_permission_level(PermissionName.PHOTO_CANCEL, False)
                if cancel_level.is_gt_lv10():
                    return status
            raise ServiceError(code=403, message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
        return status

    def _get_privacy(self, privacy=Photo.PUBLIC):
        _, privacy_level = self.get_permission_level(PermissionName.PHOTO_PRIVACY, False)
        privacy = PhotoService.choices_format(privacy, Photo.PRIVACY_CHOICES, Photo.PUBLIC)
        if privacy == Photo.PROTECTED and privacy_level.is_lt_lv1() or \
                privacy == Photo.PRIVATE and privacy_level.is_lt_lv2():
            privacy = Photo.PUBLIC
        return privacy

    def _get_read_level(self, read_level=100):
        _, read_permission_level = self.get_permission_level(PermissionName.PHOTO_READ, False)
        read_level = int(read_level) if read_level else 100
        if read_permission_level.is_lt_lv1():
            read_level = 100
        else:
            self_read_level = self.get_permission_value(PermissionName.READ_LEVEL, False)
            if read_level > self_read_level and read_permission_level.is_lt_lv10():
                read_level = self_read_level
        return read_level

    @staticmethod
    def _photo_to_dict(photo, **kwargs):
        photo_dict = model_to_dict(photo)
        author_dict = model_to_dict(photo.author)
        photo_dict['author'] = {}
        for field in UserService.USER_PUBLIC_FIELD:
            photo_dict['author'][field] = author_dict[field]
        for key in kwargs:
            photo_dict[key] = kwargs[key]
        return photo_dict
