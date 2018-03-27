#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid
import time

from django.db.models import Q

from blog.account.users.models import User
from blog.account.users.services import UserService
from blog.content.albums.models import Album
from blog.content.photos.models import Photo
from blog.common.base import Service
from blog.common.error import ServiceError
from blog.common.message import ErrorMsg, AccountErrorMsg, ContentErrorMsg
from blog.common.utils import paging, model_to_dict
from blog.common.setting import PermissionName, Setting


class AlbumService(Service):
    ALBUM_ALL_FIELD = ['id', 'uuid', 'name', 'description', 'cover',
                       'privacy', 'system', 'author', 'create_at']

    def get(self, album_uuid):
        self.has_permission(PermissionName.ALBUM_SELECT)
        try:
            album = Album.objects.get(uuid=album_uuid)
            if not self.has_get_permission(album=album):
                raise Album.DoesNotExist
            album_dict = AlbumService._album_to_dict(album=album)
        except Album.DoesNotExist:
            raise ServiceError(code=404, message=ContentErrorMsg.ALBUM_NOT_FOUND)
        return 200, album_dict

    def list(self, page=0, page_size=10, author_uuid=None, order_field=None,
             order='desc', query=None, query_field=None):
        query_level, order_level = self.get_permission_level(PermissionName.ALBUM_SELECT)
        albums = Album.objects.all()
        if author_uuid:
            albums = albums.filter(author__uuid=author_uuid)
        if order_field:
            if (order_level.is_gt_lv1() and order_field in AlbumService.ALBUM_ALL_FIELD) \
                    or order_level.is_gt_lv10():
                if order == 'desc':
                    order_field = '-' + order_field
                albums = albums.order_by(order_field)
            else:
                raise ServiceError(code=400,
                                   message=ErrorMsg.ORDER_PARAMS_ERROR)
        if query:
            if query_field and query_level.is_gt_lv1():
                if query_field == 'name':
                    query_field = 'name__icontains'
                elif query_field == 'description':
                    query_field = 'description__icontains'
                elif query_field == 'author':
                    query_field = 'author__nick__icontains'
                elif query_level.is_lt_lv10():
                    raise ServiceError(code=403,
                                       message=ErrorMsg.QUERY_PERMISSION_DENIED)
                query_dict = {query_field: query}
                albums = albums.filter(**query_dict)
            elif query_level.is_gt_lv2():
                albums = albums.filter(Q(name__icontains=query) |
                                       Q(description__icontains=query) |
                                       Q(author__nick__icontains=query))
            else:
                raise ServiceError(code=403,
                                   message=ErrorMsg.QUERY_PERMISSION_DENIED)
        for album in albums:
            if not self.has_get_permission(album=album):
                albums = albums.exclude(id=album.id)
        albums, total = paging(albums, page=page, page_size=page_size)
        return 200, {'albums': [AlbumService._album_to_dict(album=album) for album in albums], 'total': total}

    def create(self, name, description=None, cover_uuid=None, author_uuid=None,
               privacy=Album.PUBLIC, system=None):
        create_level, _ = self.get_permission_level(PermissionName.ALBUM_CREATE)
        album_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, (name + self.uuid + str(time.time())).encode('utf-8')))
        author_id = self.uid
        if author_uuid and create_level.is_gt_lv10():
            try:
                author_id = User.objects.get(uuid=author_uuid).id
            except User.DoesNotExist:
                raise ServiceError(message=AccountErrorMsg.USER_NOT_FOUND)
        cover = self._get_cover_url(user_id=author_id, cover_uuid=cover_uuid)
        if system:
            system_level, _ = self.get_permission_level(PermissionName.ALBUM_SYSTEM)
            if system_level.is_gt_lv10():
                system = AlbumService.choices_format(system, Album.SYSTEM_ALBUM_CHOICES, None)
        privacy = self._get_privacy(privacy=privacy)
        album = Album.objects.create(uuid=album_uuid,
                                     name=name,
                                     description=description,
                                     cover=cover,
                                     author_id=author_id,
                                     privacy=privacy,
                                     system=system)
        album_dict = AlbumService._album_to_dict(album=album)
        return 201, album_dict

    def update(self, album_uuid, name=None, description=None, cover_uuid=None,
               author_uuid=None, privacy=Album.PUBLIC, system=None):
        update_level, author_level = self.get_permission_level(PermissionName.ALBUM_UPDATE)
        try:
            album = Album.objects.get(uuid=album_uuid)
        except Album.DoesNotExist:
            raise ServiceError(code=404,
                               message=ContentErrorMsg.ALBUM_NOT_FOUND)
        is_self = album.author_id == self.uid
        if is_self or update_level.is_gt_lv10():
            if name:
                album.name = name
            album.update_char_field('description', description)
            if author_uuid and author_level.is_gt_lv10():
                try:
                    album.author_id = User.objects.get(uuid=author_uuid).id
                except User.DoesNotExist:
                    raise ServiceError(message=AccountErrorMsg.USER_NOT_FOUND)
            if cover_uuid is not None:
                album.cover = self._get_cover_url(user_id=album.author_id, cover_uuid=cover_uuid)
            if privacy and int(privacy) != album.privacy:
                album.privacy = self._get_privacy(privacy=privacy)
            if system is not None:
                system_level, _ = self.get_permission_level(PermissionName.ALBUM_SYSTEM)
                if system_level.is_gt_lv10():
                    album.system = AlbumService.choices_format(system, Album.SYSTEM_ALBUM_CHOICES, None)
        album.save()
        album_dict = AlbumService._album_to_dict(album=album)
        return 200, album_dict

    def delete(self, delete_id):
        delete_level, _ = self.get_permission_level(PermissionName.ALBUM_DELETE)
        result = {'id': delete_id}
        try:
            album = Album.objects.get(uuid=delete_id)
            is_self = album.author_id == self.uid
            result['name'], result['status'] = album.name, 'SUCCESS'
            if is_self and delete_level.is_gt_lv1() or delete_level.is_gt_lv10():
                album.delete()
            else:
                raise ServiceError()
        except Album.DoesNotExist:
            result['status'] = 'NOT_FOUND'
        except ServiceError:
            result['status'] = 'PERMISSION_DENIED'
        return result

    def has_get_permission(self, album):
        is_self = album.author_id == self.uid
        if is_self:
            return True
        if album.privacy == album.PUBLIC:
            return True
        get_level, _ = self.get_permission_level(PermissionName.ALBUM_PRIVACY, False)
        return get_level.is_gt_lv10()

    def _get_privacy(self, privacy=Album.PUBLIC):
        _, privacy_level = self.get_permission_level(PermissionName.ALBUM_PRIVACY, False)
        privacy = AlbumService.choices_format(privacy, Album.PRIVACY_CHOICES, Album.PUBLIC)
        if privacy == Album.PROTECTED and privacy_level.is_lt_lv1() or \
                privacy == Album.PRIVATE and privacy_level.is_lt_lv2():
            privacy = Album.PUBLIC
        return privacy

    @staticmethod
    def _get_cover_url(user_id, cover_uuid):
        if not cover_uuid:
            return None
        try:
            photo = Photo.objects.get(Q(uuid=cover_uuid, author__id=user_id) |
                                      Q(uuid=cover_uuid, album__system=Album.ALBUM_COVER_ALBUM))
            if Setting().PHOTO_THUMBNAIL and photo.image_small:
                return photo.image_small.url
            else:
                return photo.image_large.url
        except Photo.DoesNotExist:
            return None

    @staticmethod
    def _album_to_dict(album, **kwargs):
        album_dict = model_to_dict(album)
        UserService.user_to_dict(album.author, album_dict, 'author')
        for key in kwargs:
            album_dict[key] = kwargs[key]
        return album_dict
