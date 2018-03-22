#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid
import time
import os

from functools import reduce
from io import BytesIO
from PIL import Image

from django.db.models import Q
from django.utils import timezone
from django.core.files.uploadedfile import InMemoryUploadedFile

from blog.settings import MEDIA_ROOT, MEDIA_URL
from blog.account.users.services import UserService
from blog.content.albums.models import Album
from blog.content.photos.models import Photo
from blog.common.base import Service
from blog.common.error import ServiceError
from blog.common.message import ErrorMsg, ContentErrorMsg
from blog.common.utils import paging, model_to_dict
from blog.common.setting import Setting, PermissionName


class PhotoService(Service):
    PHOTO_PUBLIC_FIELD = ['id', 'uuid', 'description', 'author', 'album',
                          'status', 'privacy', 'read_level', 'like_count',
                          'dislike_count', 'create_at', 'last_editor',
                          'edit_at']

    def show(self, url):
        self.has_permission(PermissionName.PHOTO_SELECT)
        image_path = os.path.join(MEDIA_ROOT, url.replace(MEDIA_URL, ''))
        image_data = open(image_path, "rb").read()
        return 200, image_data

    def get(self, photo_uuid):
        self.has_permission(PermissionName.PHOTO_SELECT)
        try:
            photo = Photo.objects.get(uuid=photo_uuid)
            if not self._has_get_permission(photo=photo):
                raise Photo.DoesNotExist
        except Photo.DoesNotExist:
            raise ServiceError(code=404, message=ContentErrorMsg.PHOTO_NOT_FOUND)
        return 200, PhotoService._photo_to_dict(photo=photo)

    def list(self, page=0, page_size=10, album_uuid=None, author_uuid=None,
             status=None, order_field=None, order='desc', query=None,
             query_field=None):
        query_level, order_level = self.get_permission_level(PermissionName.PHOTO_SELECT)
        photos = Photo.objects.all()
        if album_uuid:
            photos = photos.filter(album__uuid=album_uuid)
        if author_uuid:
            photos = photos.filter(author__uuid=author_uuid)
        if status:
            if int(status) in dict(Photo.STATUS_CHOICES):
                photos = photos.filter(status=int(status))
            else:
                photos = photos.filter(reduce(self._status_or, list(status)))
        if order_field:
            if (order_level.is_gt_lv1() and order_field in PhotoService.PHOTO_PUBLIC_FIELD) \
                    or order_level.is_gt_lv10():
                if order == 'desc':
                    order_field = '-' + order_field
                photos = photos.order_by(order_field)
            else:
                raise ServiceError(code=400, message=ErrorMsg.ORDER_PARAMS_ERROR)
        if query:
            if query_field and query_level.is_gt_lv1():
                if query_field == 'description':
                    query_field = 'description__icontains'
                elif query_field == 'author':
                    query_field = 'author__nick__icontains'
                elif query_field == 'album':
                    query_field = 'album__name__icontains'
                elif query_field == 'status':
                    query_field = 'status'
                elif query_level.is_lt_lv10():
                    raise ServiceError(code=403,
                                       message=ErrorMsg.QUERY_PERMISSION_DENIED)
                query_dict = {query_field: query}
                photos = photos.filter(**query_dict)
            elif query_level.is_gt_lv2():
                photos = photos.filter(Q(description__icontains=query) |
                                       Q(author__nick__icontains=query) |
                                       Q(album__name__icontains=query))
            else:
                raise ServiceError(code=403, message=ErrorMsg.QUERY_PERMISSION_DENIED)
        for photo in photos:
            if not self._has_get_permission(photo=photo):
                photos = photos.exclude(id=photo.id)
        photos, total = paging(photos, page=page, page_size=page_size)
        return 200, {'photos': [PhotoService._photo_to_dict(photo) for photo in photos],
                     'total': total}

    def create(self, image, description=None, album_uuid=None, status=Photo.AUDIT,
               privacy=Photo.PUBLIC, read_level=100, origin=False, untreated=False):
        create_level, _ = self.get_permission_level(PermissionName.PHOTO_CREATE)
        count_level = self.get_permission_value(PermissionName.PHOTO_CREATE)
        if create_level.is_lt_lv10() and count_level != -1 and \
                count_level <= Photo.objects.filter(author__uid=self.uid).count():
            raise ServiceError(code=403, message=ContentErrorMsg.PHOTO_LIMIT_EXCEED)
        photo_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, (description + self.uuid + str(time.time())).encode('utf-8')))
        album = self._get_album(album_uuid=album_uuid)
        status = self._get_create_status(status=status, album=album)
        privacy = self._get_privacy(privacy=privacy)
        read_level = self._get_read_level(read_level=read_level)
        stream_large, stream_middle, stream_small = BytesIO(), BytesIO(), BytesIO()
        try:
            origin_level, untreated_level = self.get_permission_level(PermissionName.PHOTO_LIMIT)
            if origin and origin_level.is_gt_lv10():
                image_large = self._get_thumbnail(image, stream_large, 'origin', photo_uuid)
            else:
                image_large = self._get_thumbnail(image, stream_large, 'large', photo_uuid)
            if Setting().PHOTO_THUMBNAIL:
                image_middle = self._get_thumbnail(image, stream_middle, 'middle', photo_uuid)
                image_small = self._get_thumbnail(image, stream_small, 'small', photo_uuid)
            else:
                image_middle, image_small = None, None
            image_untreated = image if untreated and untreated_level.is_gt_lv10() else None
            photo = Photo.objects.create(uuid=photo_uuid,
                                         image_large=image_large,
                                         image_middle=image_middle,
                                         image_small=image_small,
                                         image_untreated=image_untreated,
                                         description=description,
                                         author_id=self.uid,
                                         album=album,
                                         status=status,
                                         privacy=privacy,
                                         read_level=read_level,
                                         last_editor_id=self.uid)
        finally:
            stream_large.close()
            stream_middle.close()
            stream_small.close()
        return 201, PhotoService._photo_to_dict(photo=photo)

    def update(self, photo_uuid, description=None, album_uuid=None,
               status=Photo.AUDIT, privacy=Photo.PUBLIC, read_level=100,
               like_count=None, dislike_count=None):
        update_level, _ = self.get_permission_level(PermissionName.PHOTO_UPDATE)
        try:
            photo = Photo.objects.get(uuid=photo_uuid)
        except Photo.DoesNotExist:
            raise ServiceError(code=404, message=ContentErrorMsg.PHOTO_NOT_FOUND)
        if like_count or dislike_count:
            _, read_permission = self._has_get_permission(photo=photo)
            # Todo photo like list
            pass
        is_self = photo.author_id == self.uid
        is_content_change, is_edit = False, False
        if is_self and update_level.is_gt_lv1() or update_level.is_gt_lv10():
            if description is not None and description != photo.description:
                photo.update_char_field('description', description)
                is_content_change = True
            if album_uuid is not None and album_uuid != photo.album.uuid:
                photo.album = self._get_album(album_uuid=album_uuid)
            if privacy and int(privacy) != photo.privacy:
                photo.privacy, is_edit = self._get_privacy(privacy=privacy), True
            if read_level and int(read_level) != photo.read_level:
                photo.read_level, is_edit = self._get_read_level(read_level=read_level), True
        else:
            raise ServiceError(code=403, message=ErrorMsg.PERMISSION_DENIED)
        if is_content_change or is_edit:
            photo.last_editor_id = self.uid
            photo.edit_at = timezone.now()
        if status and int(status) != photo.status:
            photo.status = self._get_update_status(status, photo, is_content_change)
        elif is_content_change:
            _, audit_level = self.get_permission_level(PermissionName.PHOTO_AUDIT, False)
            if audit_level.is_lt_lv10() and \
                (photo.status == Photo.ACTIVE or
                 photo.status == Photo.AUDIT or
                 photo.status == Photo.FAILED):
                photo.status = status if Setting().PHOTO_AUDIT else photo.status
        photo.save()
        return 200, PhotoService._photo_to_dict(photo=photo)

    def _has_get_permission(self, photo):
        is_author = photo.author_id == self.uid
        if is_author and photo.status != Photo.CANCEL:
            return True
        permission_level, _ = self.get_permission_level(PermissionName.PHOTO_PERMISSION, False)
        if permission_level.is_gt_lv10():
            return True
        if photo.status == Photo.ACTIVE:
            privacy_level, _ = self.get_permission_level(PermissionName.PHOTO_PRIVACY, False)
            read_permission_level, _ = self.get_permission_level(PermissionName.PHOTO_READ, False)
            read_level = self.get_permission_value(PermissionName.READ_LEVEL, False)
            return (photo.privacy == Photo.PUBLIC or privacy_level.is_gt_lv10()) and \
                (read_level >= photo.read_level or read_permission_level.is_gt_lv10())
        elif photo.status == Photo.CANCEL:
            cancel_level, _ = self.get_permission_level(PermissionName.PHOTO_CANCEL, False)
            return cancel_level.is_gt_lv10()
        elif photo.status == Photo.AUDIT or photo.status == Photo.FAILED:
            audit_level, _ = self.get_permission_level(PermissionName.ARTICLE_AUDIT, False)
            return audit_level.is_gt_lv10()
        return False

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

    def _get_update_status(self, status, photo, is_content_change):
        default = photo.status
        is_self = photo.author_id == self.uid
        status = PhotoService.choices_format(status, Photo.STATUS_CHOICES, default)
        if status == photo.status and (status != Photo.ACTIVE and
                                       status != Photo.FAILED or
                                       (status == Photo.ACTIVE or
                                        status == Photo.FAILED) and
                                       not is_content_change):
            return status
        if status == Photo.ACTIVE or status == Photo.AUDIT or status == Photo.FAILED:
            if Setting().ARTICLE_AUDIT:
                if is_content_change and status == Photo.AUDIT:
                    return status
                _, audit_level = self.get_permission_level(PermissionName.ARTICLE_AUDIT, False)
                if audit_level.is_gt_lv10():
                    return status
                if is_self and (status == Photo.ACTIVE or status == Photo.FAILED):
                    return Photo.AUDIT
                raise ServiceError(code=403, message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
            elif status == Photo.ACTIVE:
                return status
        elif status == Photo.CANCEL:
            if Setting().ARTICLE_CANCEL:
                _, cancel_level = self.get_permission_level(PermissionName.ARTICLE_CANCEL, False)
                if cancel_level.is_gt_lv10():
                    return status
        elif status == Photo.RECYCLED:
            if is_self:
                return status
        raise ServiceError(code=403, message=ContentErrorMsg.STATUS_PERMISSION_DENIED)

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
    def _get_thumbnail(image, stream, size, photo_uuid='pic'):
        pil_image = Image.open(image)
        pil_format = pil_image.format.lower()
        if pil_format not in ('jpeg', 'png', 'gif'):
            pil_format = 'jpeg'
        content_type = 'image/' + pil_format
        image_name = photo_uuid + '.' + pil_format
        setting = Setting()
        if size == 'large':
            pil_image.thumbnail((setting.PHOTO_LARGE_SIZE, setting.PHOTO_LARGE_SIZE), Image.ANTIALIAS)
        elif size == 'middle':
            pil_image.thumbnail((setting.PHOTO_MIDDLE_SIZE, setting.PHOTO_MIDDLE_SIZE), Image.ANTIALIAS)
        elif size == 'small':
            pil_image.thumbnail((setting.PHOTO_SMALL_SIZE, setting.PHOTO_SMALL_SIZE), Image.ANTIALIAS)
        elif size != 'origin':
            raise ServiceError(code=500, message=ErrorMsg.REQUEST_PARAMS_ERROR)
        pil_image.save(stream, format=pil_format)
        return InMemoryUploadedFile(stream, None, image_name,
                                    content_type, stream.tell(), {})

    @staticmethod
    def _photo_to_dict(photo, **kwargs):
        photo_dict = model_to_dict(photo)
        author_dict = model_to_dict(photo.author)
        photo_dict['author'] = {}
        for field in UserService.USER_PUBLIC_FIELD:
            photo_dict['author'][field] = author_dict[field]
        last_editor_dict = model_to_dict(photo.last_editor)
        photo_dict['last_editor'] = {}
        for field in UserService.USER_PUBLIC_FIELD:
            photo_dict['last_editor'][field] = last_editor_dict[field]
        for key in kwargs:
            photo_dict[key] = kwargs[key]
        return photo_dict
