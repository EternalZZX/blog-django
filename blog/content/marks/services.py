#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid
import time

from django.db.models import Q

from blog.account.users.models import User
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
from blog.common.message import ErrorMsg, AccountErrorMsg, ContentErrorMsg
from blog.common.utils import paging, str_to_list, model_to_dict
from blog.common.setting import PermissionName


class MarkService(Service):
    MARK_ORDER_FIELD = ['id', 'name', 'description', 'author', 'color',
                        'attach_count', 'privacy', 'create_at']
    OPERATE_ATTACH = 1
    OPERATE_DETACH = 0

    def get(self, mark_uuid):
        self.has_permission(PermissionName.MARK_SELECT)
        try:
            mark = Mark.objects.get(uuid=mark_uuid)
            if not self._has_get_permission(mark=mark):
                raise Mark.DoesNotExist
        except Mark.DoesNotExist:
            raise ServiceError(code=404, message=ContentErrorMsg.MARK_NOT_FOUND)
        resources = MarkResource.objects.filter(mark=mark)
        return 200, MarkService._mark_to_dict(mark=mark, resources=resources)

    def list(self, page=0, page_size=10, author_uuid=None, resource_type=None,
             resource_uuid=None, order_field=None, order='desc',
             query=None, query_field=None):
        query_level, order_level = self.get_permission_level(PermissionName.MARK_SELECT)
        marks = Mark.objects.all()
        if author_uuid:
            marks = marks.filter(author__uuid=author_uuid)
        if resource_type is not None and resource_uuid:
            resources = MarkResource.objects.filter(resource_type=resource_type,
                                                    resource_uuid=resource_uuid)
            marks = self.query_by_list(marks, [{'id': resource.mark_id} for resource in resources])
        if order_field:
            if (order_level.is_gt_lv1() and order_field in MarkService.MARK_ORDER_FIELD) \
                    or order_level.is_gt_lv10():
                if order == 'desc':
                    order_field = '-' + order_field
                    marks = marks.order_by(order_field)
            else:
                raise ServiceError(code=400, message=ErrorMsg.ORDER_PARAMS_ERROR)
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
                elif query_field == 'color':
                    query_field = 'color'
                elif query_level.is_lt_lv10():
                    raise ServiceError(code=403,
                                       message=ErrorMsg.QUERY_PERMISSION_DENIED)
                marks = self.query_by_list(marks, [{query_field: item} for item in str_to_list(query)])
            elif query_level.is_gt_lv2():
                marks = marks.filter(Q(uuid=query) |
                                     Q(name__icontains=query) |
                                     Q(description__icontains=query) |
                                     Q(author__nick__icontains=query) |
                                     Q(color=query))
            else:
                raise ServiceError(code=403,
                                   message=ErrorMsg.QUERY_PERMISSION_DENIED)
        for mark in marks:
            if not self._has_get_permission(mark=mark):
                marks = marks.exclude(id=mark.id)
        marks, total = paging(marks, page=page, page_size=page_size)
        return 200, {'marks': [MarkService._mark_to_dict(mark=mark) for mark in marks],
                     'total': total}

    def create(self, name, description=None, color=None, privacy=Mark.PUBLIC,
               author_uuid=None, resource_type=None, resource_uuid=None):
        create_level, _ = self.get_permission_level(PermissionName.MARK_CREATE)
        mark_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, (name + self.uuid + str(time.time())).encode('utf-8')))
        privacy = self._get_privacy(privacy=privacy)
        author_id = self.uid
        if author_uuid and create_level.is_gt_lv10():
            try:
                author_id = User.objects.get(uuid=author_uuid).id
            except User.DoesNotExist:
                raise ServiceError(message=AccountErrorMsg.USER_NOT_FOUND)
        mark = Mark.objects.create(uuid=mark_uuid,
                                   name=name,
                                   description=description,
                                   color=color,
                                   privacy=privacy,
                                   author_id=author_id)
        resource = self._attach_resource(mark, resource_type, resource_uuid)
        resources = [resource] if resource else []
        return 201, MarkService._mark_to_dict(mark=mark, resources=resources)

    def update(self, mark_uuid, name=None, description=None, color=None,
               privacy=None, author_uuid=None, operate=None, resource_type=None,
               resource_uuid=None):
        update_level, author_level = self.get_permission_level(PermissionName.MARK_UPDATE)
        try:
            mark = Mark.objects.get(uuid=mark_uuid)
        except Mark.DoesNotExist:
            raise ServiceError(code=404, message=ContentErrorMsg.MARK_NOT_FOUND)
        is_self = mark.author_id == self.uid
        if is_self or update_level.is_gt_lv10():
            if name:
                mark.name = name
            mark.update_char_field('description', description)
            mark.update_char_field('color', color)
            if privacy and int(privacy) != mark.privacy:
                mark.privacy = self._get_privacy(privacy=privacy)
            if author_uuid and author_level.is_gt_lv10():
                try:
                    mark.author_id = User.objects.get(uuid=author_uuid).id
                except User.DoesNotExist:
                    raise ServiceError(message=AccountErrorMsg.USER_NOT_FOUND)
        else:
            raise ServiceError(code=403, message=ErrorMsg.PERMISSION_DENIED)
        mark.save()
        if operate is not None:
            if int(operate) == MarkService.OPERATE_ATTACH:
                self._attach_resource(mark, resource_type, resource_uuid)
            elif int(operate) == MarkService.OPERATE_DETACH:
                self._detach_resource(mark, resource_type, resource_uuid)
        resources = MarkResource.objects.filter(mark=mark)
        mark.attach_count = len(resources)
        return 200, MarkService._mark_to_dict(mark=mark, resources=resources)

    def delete(self, delete_id):
        delete_level, _ = self.get_permission_level(PermissionName.MARK_DELETE)
        result = {'id': delete_id}
        try:
            mark = Mark.objects.get(uuid=delete_id)
            is_self = mark.author_id == self.uid
            result['name'], result['status'] = mark.name, 'SUCCESS'
            if is_self and delete_level.is_gt_lv1() or delete_level.is_gt_lv10():
                mark.delete()
            else:
                raise ServiceError()
        except Mark.DoesNotExist:
            result['status'] = 'NOT_FOUND'
        except ServiceError:
            result['status'] = 'PERMISSION_DENIED'
        return result

    def _has_get_permission(self, mark):
        is_self = mark.author_id == self.uid
        if is_self:
            return True
        if mark.privacy == mark.PUBLIC:
            return True
        get_level, _ = self.get_permission_level(PermissionName.MARK_PRIVACY, False)
        return get_level.is_gt_lv10()

    def _attach_resource(self, mark, resource_type, resource_uuid):
        if resource_type is None or not resource_uuid:
            return None
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
        resource, created = MarkResource.objects.get_or_create(mark=mark,
                                                               resource_type=resource_type,
                                                               resource_uuid=resource_uuid)
        return resource

    def _detach_resource(self, mark, resource_type, resource_uuid):
        if resource_type is None or not resource_uuid:
            return
        resources = MarkResource.objects.filter(mark=mark,
                                                resource_type=resource_type,
                                                resource_uuid=resource_uuid)
        resources.delete()

    def _get_privacy(self, privacy=Mark.PUBLIC):
        _, privacy_level = self.get_permission_level(PermissionName.MARK_PRIVACY, False)
        privacy = MarkService.choices_format(privacy, Mark.PRIVACY_CHOICES, Mark.PUBLIC)
        if privacy == Mark.PRIVATE and privacy_level.is_lt_lv1():
            privacy = Mark.PUBLIC
        return privacy

    @staticmethod
    def _mark_to_dict(mark, resources=None, **kwargs):
        mark_dict = model_to_dict(mark)
        UserService.user_to_dict(mark.author, mark_dict, 'author')
        if resources is not None:
            resource_dict_list = []
            for resource in resources:
                resource_dict_list.append({
                    'resource_type': resource.resource_type,
                    'resource_uuid': resource.resource_uuid
                })
            mark_dict['resources'] = resource_dict_list
        for key in kwargs:
            mark_dict[key] = kwargs[key]
        return mark_dict
