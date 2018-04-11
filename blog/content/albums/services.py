#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid
import time

from django.db.models import Q

from blog.account.users.models import User
from blog.account.users.services import UserService
from blog.content.albums.models import Album
from blog.content.photos.models import Photo
from blog.common.base import Service, MetadataService
from blog.common.error import ServiceError
from blog.common.message import ErrorMsg, AccountErrorMsg, ContentErrorMsg
from blog.common.utils import paging, str_to_list, model_to_dict
from blog.common.setting import PermissionName, Setting


class AlbumService(Service):
    ALBUM_ORDER_FIELD = ['id', 'name', 'description', 'privacy', 'system',
                         'author', 'create_at', 'read_count', 'comment_count',
                         'like_count', 'dislike_count']
    METADATA_ORDER_FIELD = ['read_count', 'comment_count', 'like_count',
                            'dislike_count']

    def get(self, album_uuid, like_list_type=None, like_list_start=0, like_list_end=10):
        self.has_permission(PermissionName.ALBUM_SELECT)
        try:
            album = Album.objects.get(uuid=album_uuid)
            if not self.has_get_permission(album=album):
                raise Album.DoesNotExist
        except Album.DoesNotExist:
            raise ServiceError(code=404, message=ContentErrorMsg.ALBUM_NOT_FOUND)
        if like_list_type is None:
            metadata = AlbumMetadataService().update_metadata_count(resource=album,
                                                                    read_count=AlbumMetadataService.OPERATE_ADD)
            is_like_user = AlbumMetadataService().is_like_user(resource=album, user_id=self.uid)
            album_dict = AlbumService._album_to_dict(album=album,
                                                     metadata=metadata,
                                                     is_like_user=is_like_user)
        else:
            like_level, _ = self.get_permission_level(PermissionName.ALBUM_LIKE)
            if like_level.is_gt_lv10() or like_level.is_gt_lv1() and \
                    int(like_list_type) == AlbumMetadataService.LIKE_LIST:
                metadata, like_user_dict = AlbumMetadataService().get_metadata_dict(
                    resource=album, start=like_list_start, end=like_list_end, list_type=like_list_type)
                album_dict = AlbumService._album_to_dict(album=album, metadata=metadata, **like_user_dict)
            else:
                raise ServiceError(code=403, message=ErrorMsg.PERMISSION_DENIED)
        return 200, album_dict

    def list(self, page=0, page_size=10, author_uuid=None, order_field=None,
             order='desc', query=None, query_field=None):
        query_level, order_level = self.get_permission_level(PermissionName.ALBUM_SELECT)
        albums = Album.objects.all()
        if author_uuid:
            albums = albums.filter(author__uuid=author_uuid)
        if order_field:
            if (order_level.is_gt_lv1() and order_field in AlbumService.ALBUM_ORDER_FIELD) \
                    or order_level.is_gt_lv10():
                if order_field in AlbumService.METADATA_ORDER_FIELD:
                    order_field = 'metadata__' + order_field
                if order == 'desc':
                    order_field = '-' + order_field
                albums = albums.order_by(order_field)
            else:
                raise ServiceError(code=400,
                                   message=ErrorMsg.ORDER_PARAMS_ERROR)
        if query:
            if query_field and query_level.is_gt_lv1():
                if query_field == 'uuid':
                    query_field = 'uuid'
                elif query_field == 'name':
                    query_field = 'name__icontains'
                elif query_field == 'description':
                    query_field = 'description__icontains'
                elif query_field == 'author':
                    query_field = 'author__nick__icontains'
                elif query_level.is_lt_lv10():
                    raise ServiceError(code=403,
                                       message=ErrorMsg.QUERY_PERMISSION_DENIED)
                albums = self.query_by_list(albums, [{query_field: item} for item in str_to_list(query)])
            elif query_level.is_gt_lv2():
                albums = albums.filter(Q(uuid=query) |
                                       Q(name__icontains=query) |
                                       Q(description__icontains=query) |
                                       Q(author__nick__icontains=query))
            else:
                raise ServiceError(code=403,
                                   message=ErrorMsg.QUERY_PERMISSION_DENIED)
        for album in albums:
            if not self.has_get_permission(album=album):
                albums = albums.exclude(id=album.id)
        albums, total = paging(albums, page=page, page_size=page_size)
        album_dict_list = []
        for album in albums:
            metadata = AlbumMetadataService().get_metadata_count(resource=album)
            album_dict = AlbumService._album_to_dict(album=album, metadata=metadata)
            album_dict_list.append(album_dict)
        return 200, {'albums': album_dict_list, 'total': total}

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
               author_uuid=None, privacy=None, system=None, like_operate=None):
        update_level, author_level = self.get_permission_level(PermissionName.ALBUM_UPDATE)
        try:
            album = Album.objects.get(uuid=album_uuid)
        except Album.DoesNotExist:
            raise ServiceError(code=404,
                               message=ContentErrorMsg.ALBUM_NOT_FOUND)
        if like_operate is not None:
            metadata = self._update_like_list(album=album, operate=like_operate)
            return 200, AlbumService._album_to_dict(album=album, metadata=metadata)
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
        metadata = AlbumMetadataService().get_metadata_count(resource=album)
        return 200, AlbumService._album_to_dict(album=album, metadata=metadata)

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

    def _update_like_list(self, album, operate):
        _, like_level = self.get_permission_level(PermissionName.ALBUM_LIKE)
        if like_level.is_lt_lv1():
            raise ServiceError(code=403, message=ErrorMsg.PERMISSION_DENIED)
        _, read_permission = self.has_get_permission(album=album)
        if not read_permission:
            raise ServiceError(code=403, message=ErrorMsg.PERMISSION_DENIED)
        return AlbumMetadataService().update_like_list(resource=album, user_id=self.uid, operate=operate)

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
    def _album_to_dict(album, metadata=None, **kwargs):
        album_dict = model_to_dict(album)
        UserService.user_to_dict(album.author, album_dict, 'author')
        album_dict['metadata'] = {}
        album_dict['metadata']['read_count'] = metadata.read_count if metadata else 0
        album_dict['metadata']['comment_count'] = metadata.comment_count if metadata else 0
        album_dict['metadata']['like_count'] = metadata.like_count if metadata else 0
        album_dict['metadata']['dislike_count'] = metadata.dislike_count if metadata else 0
        for key in kwargs:
            album_dict[key] = kwargs[key]
        return album_dict


class AlbumMetadataService(MetadataService):
    METADATA_KEY = 'ALBUM_METADATA'
    LIKE_LIST_KEY = 'ALBUM_LIKE_LIST'
    DISLIKE_LIST_KEY = 'ALBUM_DISLIKE_LIST'

    def get_metadata_dict(self, resource, start=0, end=-1, list_type=MetadataService.LIKE_LIST):
        metadata, like_user_ids, dislike_user_ids = self.get_metadata(resource=resource,
                                                                      start=start,
                                                                      end=end,
                                                                      list_type=list_type)
        user_dict = {}
        if like_user_ids is not None:
            like_users = [UserService.get_user_dict(user_id=user_id) for user_id in like_user_ids]
            user_dict['like_users'] = like_users
        if dislike_user_ids is not None:
            dislike_users = [UserService.get_user_dict(user_id=user_id) for user_id in dislike_user_ids]
            user_dict['dislike_users'] = dislike_users
        return metadata, user_dict

    def _set_sql_metadata(self, resource_uuid, metadata):
        like_list_key, dislike_list_key = self._get_like_list_key(resource_uuid)
        try:
            album = Album.objects.get(uuid=resource_uuid)
            self._set_resource_sql_metadata(album, metadata, like_list_key, dislike_list_key)
        except Album.DoesNotExist:
            self.redis_client.hash_delete(self.METADATA_KEY, resource_uuid)
            self.redis_client.delete(like_list_key, dislike_list_key)
