#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid
import time

from django.db.models import Q

from blog.account.users.services import UserService
from blog.content.comments.models import Comment
from blog.content.sections.services import SectionService
from blog.content.articles.models import Article
from blog.content.albums.models import Album
from blog.content.photos.models import Photo
from blog.common.base import Service
from blog.common.error import ServiceError
from blog.common.message import ErrorMsg, ContentErrorMsg
from blog.common.utils import paging, model_to_dict
from blog.common.setting import Setting, PermissionName


class CommentService(Service):
    def create(self, resource_type, resource_uuid, content=None, status=Comment.AUDIT):
        self.has_permission(PermissionName.COMMENT_CREATE)
        comment_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS,
                                      (resource_uuid + self.uuid + str(time.time())).encode('utf-8')))
        resource, section = self._get_resource(resource_type, resource_uuid)
        status = self._get_create_status(status=status, section=section)
        comment = Comment.objects.create(uuid=comment_uuid,
                                         resource_type=resource_type,
                                         resource_uuid=resource_uuid,
                                         resource_author_id=resource.author_id,
                                         resource_section=section,
                                         content=content,
                                         author_id=self.uid,
                                         status=status,
                                         last_editor_id=self.uid)
        return 201, CommentService._comment_to_dict(comment=comment)

    def _get_create_status(self, status, section):
        default = Comment.AUDIT if Setting().COMMENT_AUDIT else Comment.ACTIVE
        status = CommentService.choices_format(status, Comment.STATUS_CHOICES, default)
        if status == Comment.AUDIT:
            return default
        if status == Comment.ACTIVE or status == Comment.FAILED:
            if Setting().COMMENT_AUDIT:
                _, audit_level = self.get_permission_level(PermissionName.COMMENT_AUDIT, False)
                if audit_level.is_gt_lv10():
                    return status
                if section:
                    set_role = SectionService.is_manager(user_uuid=self.uuid, section=section)
                    if SectionService.has_set_permission(permission=section.sectionpermission.comment_audit,
                                                         set_role=set_role):
                        return status
                raise ServiceError(code=403, message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
            elif status == Comment.ACTIVE:
                return Comment.ACTIVE
            raise ServiceError(code=403, message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
        if status == Comment.CANCEL:
            if Setting().COMMENT_CANCEL:
                _, cancel_level = self.get_permission_level(PermissionName.COMMENT_CANCEL, False)
                if cancel_level.is_gt_lv10():
                    return status
                if section:
                    set_role = SectionService.is_manager(user_uuid=self.uuid, section=section)
                    if SectionService.has_set_permission(permission=section.sectionpermission.comment_cancel,
                                                         set_role=set_role):
                        return status
            raise ServiceError(code=403, message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
        return status

    @staticmethod
    def _get_resource(resource_type, resource_uuid):
        resource_type = CommentService.choices_format(resource_type, Comment.TYPE_CHOICES, None)
        try:
            section = None
            if resource_type == Comment.ARTICLE:
                resource = Article.objects.get(uuid=resource_uuid)
                section = resource.section
            elif resource_type == Comment.COMMENT:
                resource = Comment.objects.get(uuid=resource_uuid)
                section = resource.resource_section
            elif resource_type == Comment.ALBUM:
                resource = Album.objects.get(uuid=resource_uuid)
            elif resource_type == Comment.PHOTO:
                resource = Photo.objects.get(uuid=resource_uuid)
            else:
                raise ServiceError(message=ErrorMsg.REQUEST_PARAMS_ERROR)
        except (Article.DoesNotExist, Comment.DoesNotExist,
                Album.DoesNotExist, Photo.DoesNotExist):
            raise ServiceError(code=404, message=ContentErrorMsg.RESOURCE_NOT_FOUND)
        return resource, section

    @staticmethod
    def _comment_to_dict(comment, **kwargs):
        comment_dict = model_to_dict(comment)
        author_dict = model_to_dict(comment.author)
        comment_dict['author'] = {}
        for field in UserService.USER_PUBLIC_FIELD:
            comment_dict['author'][field] = author_dict[field]
        last_editor_dict = model_to_dict(comment.last_editor)
        comment_dict['last_editor'] = {}
        for field in UserService.USER_PUBLIC_FIELD:
            comment_dict['last_editor'][field] = last_editor_dict[field]
        for key in kwargs:
            comment_dict[key] = kwargs[key]
        return comment_dict
