#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid
import time

from django.db.models import Q

from blog.account.users.services import UserService
from blog.content.comments.models import Comment
from blog.content.sections.services import SectionService
from blog.content.articles.models import Article
from blog.content.articles.services import ArticleService
from blog.content.albums.models import Album
from blog.content.albums.services import AlbumService
from blog.content.photos.models import Photo
from blog.content.photos.services import PhotoService
from blog.common.base import Service
from blog.common.error import ServiceError
from blog.common.message import ErrorMsg, ContentErrorMsg
from blog.common.utils import paging, model_to_dict
from blog.common.setting import Setting, PermissionName


class CommentService(Service):
    def get(self, comment_uuid):
        self.has_permission(PermissionName.COMMENT_SELECT)
        try:
            comment = Comment.objects.get(uuid=comment_uuid)
            if not self._has_get_permission(comment=comment):
                raise Comment.DoesNotExist
        except Comment.DoesNotExist:
            raise ServiceError(code=404, message=ContentErrorMsg.COMMENT_NOT_FOUND)
        return 200, CommentService._comment_to_dict(comment=comment)

    def create(self, resource_type, resource_uuid, reply_uuid=None,
               content=None, status=Comment.AUDIT):
        self.has_permission(PermissionName.COMMENT_CREATE)
        resource_type = CommentService.choices_format(resource_type, Comment.TYPE_CHOICES, None)
        resource, section = self._get_resource(resource_type, resource_uuid)
        parent_uuid, reply_user_id = self._get_reply(reply_uuid=reply_uuid)
        comment_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS,
                                      (resource_uuid + self.uuid + str(time.time())).encode('utf-8')))
        status = self._get_create_status(status=status, section=section)
        comment = Comment.objects.create(uuid=comment_uuid,
                                         resource_type=resource_type,
                                         resource_uuid=resource_uuid,
                                         resource_author_id=resource.author_id,
                                         resource_section=section,
                                         parent_uuid=parent_uuid,
                                         reply_user_id=reply_user_id,
                                         content=content,
                                         author_id=self.uid,
                                         status=status,
                                         last_editor_id=self.uid)
        return 201, CommentService._comment_to_dict(comment=comment)

    def _has_get_permission(self, comment):
        section = comment.resource_section
        is_author = comment.author_id == self.uid
        if is_author and comment.status != Comment.CANCEL:
            return True
        permission_level, _ = self.get_permission_level(PermissionName.COMMENT_PERMISSION, False)
        if permission_level.is_gt_lv10():
            return True
        if section:
            _, read_permission = SectionService(request=self.request, instance=self).has_get_permission(section)
            if not read_permission:
                return False
        if comment.status == Comment.ACTIVE:
            return True
        elif comment.status == Comment.CANCEL:
            cancel_level, _ = self.get_permission_level(PermissionName.COMMENT_CANCEL, False)
            if cancel_level.is_gt_lv10():
                return True
            if section:
                set_role = SectionService.is_manager(user_uuid=self.uuid, section=section)
                if SectionService.has_set_permission(permission=section.sectionpermission.comment_delete,
                                                     set_role=set_role):
                    return True
        elif comment.status == Comment.AUDIT or comment.status == Comment.FAILED:
            audit_level, _ = self.get_permission_level(PermissionName.COMMENT_AUDIT, False)
            if audit_level.is_gt_lv10():
                return True
            if section:
                set_role = SectionService.is_manager(user_uuid=self.uuid, section=section)
                if SectionService.has_set_permission(permission=section.sectionpermission.comment_audit,
                                                     set_role=set_role):
                    return True
        elif section and comment.status == Comment.RECYCLED:
            set_role = SectionService.is_manager(user_uuid=self.uuid, section=section)
            if SectionService.has_set_permission(permission=section.sectionpermission.comment_recycled,
                                                 set_role=set_role):
                return True
        return False

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

    def _get_resource(self, resource_type, resource_uuid):
        try:
            section = None
            if resource_type == Comment.ARTICLE:
                resource = Article.objects.get(uuid=resource_uuid)
                _, read_permission = ArticleService(request=self.request,
                                                    instance=self).has_get_permission(article=resource)
                section = resource.section
            elif resource_type == Comment.ALBUM:
                resource = Album.objects.get(uuid=resource_uuid)
                read_permission = AlbumService(request=self.request,
                                               instance=self).has_get_permission(album=resource)
            elif resource_type == Comment.PHOTO:
                resource = Photo.objects.get(uuid=resource_uuid)
                read_permission = PhotoService(request=self.request,
                                               instance=self).has_get_permission(photo=resource)
            else:
                raise ServiceError(message=ErrorMsg.REQUEST_PARAMS_ERROR)
            if not read_permission:
                raise ServiceError(code=404, message=ContentErrorMsg.RESOURCE_NOT_FOUND)
        except (Article.DoesNotExist, Comment.DoesNotExist,
                Album.DoesNotExist, Photo.DoesNotExist):
            raise ServiceError(code=404, message=ContentErrorMsg.RESOURCE_NOT_FOUND)
        return resource, section

    def _get_reply(self, reply_uuid):
        parent_uuid, reply_user_id = None, None
        if reply_uuid:
            try:
                reply_comment = Comment.objects.get(uuid=reply_uuid)
                if reply_comment.author_id == self.uid:
                    raise ServiceError(message=ContentErrorMsg.COMMENT_REPLY_ERROR)
                if reply_comment.parent_uuid and reply_comment.reply_user_id == self.uid:
                    parent_uuid = reply_comment.parent_uuid
                else:
                    parent_uuid = reply_uuid
                reply_user_id = reply_comment.author_id
            except Comment.DoesNotExist:
                raise ServiceError(code=404, message=ContentErrorMsg.COMMENT_NOT_FOUND)
        return parent_uuid, reply_user_id

    @staticmethod
    def _comment_to_dict(comment, **kwargs):
        comment_dict = model_to_dict(comment)
        if comment.reply_user:
            UserService.user_to_dict(comment.reply_user, comment_dict, 'reply_user')
        UserService.user_to_dict(comment.author, comment_dict, 'author')
        UserService.user_to_dict(comment.last_editor, comment_dict, 'last_editor')
        for key in kwargs:
            comment_dict[key] = kwargs[key]
        return comment_dict
