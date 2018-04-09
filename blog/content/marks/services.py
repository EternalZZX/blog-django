#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

from functools import reduce

from django.db.models import Q
from django.utils import timezone

from blog.account.users.services import UserService
from blog.content.articles.models import Article
from blog.content.articles.services import ArticleService
from blog.content.albums.models import Album
from blog.content.albums.services import AlbumService
from blog.content.photos.models import Photo
from blog.content.photos.services import PhotoService
from blog.content.marks.models import Mark, MarkResource
from blog.common.base import Service
from blog.common.error import ServiceError
from blog.common.message import ErrorMsg, ContentErrorMsg
from blog.common.utils import paging, model_to_dict
from blog.common.setting import Setting, PermissionName


class MarkService(Service):
    def get(self, mark_id):
        self.has_permission(PermissionName.MARK_SELECT)
        try:
            mark = Mark.objects.get(id=mark_id)
            if not self._has_get_permission(mark=mark):
                raise Mark.DoesNotExist
        except Mark.DoesNotExist:
            raise ServiceError(code=404, message=ContentErrorMsg.MARK_NOT_FOUND)
        return 200, MarkService._mark_to_dict(mark=mark)

    def create(self, name, description=None, color=None, privacy=Mark.PUBLIC,
               resource_type=None, resource_uuid=None):
        self.has_permission(PermissionName.MARK_CREATE)
        privacy = self._get_privacy(privacy=privacy)
        mark = Mark.objects.create(name=name,
                                   description=description,
                                   color=color,
                                   privacy=privacy)
        if resource_type is not None and resource_uuid:
            self._attach_resource(mark=mark,
                                  resource_type=resource_type,
                                  resource_uuid=resource_uuid)
        return 201, MarkService._mark_to_dict(mark=mark)

    def _has_get_permission(self, mark):
        is_self = mark.author_id == self.uid
        if is_self:
            return True
        if mark.privacy == mark.PUBLIC:
            return True
        get_level, _ = self.get_permission_level(PermissionName.MARK_PRIVACY, False)
        return get_level.is_gt_lv10()

    def _attach_resource(self, mark, resource_type, resource_uuid):
        try:
            resource_type = int(resource_type)
            if resource_type == MarkResource.ARTICLE:
                resource = Article.objects.get(uuid=resource_uuid)
                _, read_permission = ArticleService(request=self.request,
                                                    instance=self).has_get_permission(article=resource)
            elif resource_type == MarkResource.ALBUM:
                resource = Album.objects.get(uuid=resource_uuid)
                read_permission = AlbumService(request=self.request,
                                               instance=self).has_get_permission(album=resource)
            elif resource_type == MarkResource.PHOTO:
                resource = Photo.objects.get(uuid=resource_uuid)
                read_permission = PhotoService(request=self.request,
                                               instance=self).has_get_permission(photo=resource)
            else:
                raise ServiceError(message=ErrorMsg.REQUEST_PARAMS_ERROR)
            if not read_permission:
                raise ServiceError(code=404, message=ContentErrorMsg.RESOURCE_NOT_FOUND)
        except (Article.DoesNotExist, Album.DoesNotExist, Photo.DoesNotExist):
            raise ServiceError(code=404, message=ContentErrorMsg.RESOURCE_NOT_FOUND)
        try:
            MarkResource.objects.get(mark=mark,
                                     resource_type=resource_type,
                                     resource_uuid=resource_uuid)
        except MarkResource.DoesNotExist:
            MarkResource.objects.create(mark=mark,
                                        resource_type=resource_type,
                                        resource_uuid=resource_uuid)
            mark.attach_mark()

    def _get_privacy(self, privacy=Mark.PUBLIC):
        _, privacy_level = self.get_permission_level(PermissionName.MARK_PRIVACY, False)
        privacy = MarkService.choices_format(privacy, Mark.PRIVACY_CHOICES, Mark.PUBLIC)
        if privacy == Mark.PRIVATE and privacy_level.is_lt_lv1():
            privacy = Mark.PUBLIC
        return privacy

    @staticmethod
    def _mark_to_dict(mark, **kwargs):
        mark_dict = model_to_dict(mark)
        UserService.user_to_dict(mark.author, mark_dict, 'author')
        for key in kwargs:
            mark_dict[key] = kwargs[key]
        return mark_dict
