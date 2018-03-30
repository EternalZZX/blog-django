#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid
import time

from functools import reduce

from django.db.models import Q
from django.utils import timezone

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
    COMMENT_PUBLIC_FIELD = ['id', 'uuid', 'resource_type', 'resource_uuid',
                            'resource_author', 'resource_section', 'dialog_uuid',
                            'reply_comment', 'content', 'author', 'status',
                            'like_count', 'dislike_count', 'create_at',
                            'last_editor', 'edit_at']

    def get(self, comment_uuid):
        self.has_permission(PermissionName.COMMENT_SELECT)
        try:
            comment = Comment.objects.get(uuid=comment_uuid)
            if not self._has_get_permission(comment=comment):
                raise Comment.DoesNotExist
        except Comment.DoesNotExist:
            raise ServiceError(code=404, message=ContentErrorMsg.COMMENT_NOT_FOUND)
        return 200, CommentService._comment_to_dict(comment=comment)

    def list(self, page=0, page_size=10, resource_type=None, resource_uuid=None,
             resource_section_id=None, dialog_uuid=None, reply_uuid=None,
             author_uuid=None, status=None, order_field=None, order='desc',
             query=None, query_field=None):
        query_level, order_level = self.get_permission_level(PermissionName.COMMENT_SELECT)
        comments = Comment.objects.all()
        if resource_type and int(resource_type) in dict(Comment.TYPE_CHOICES):
            comments = comments.filter(resource_type=int(resource_type))
        if resource_uuid:
            comments = comments.filter(resource_uuid=resource_uuid)
        if resource_section_id:
            comments = comments.filter(resource_section_id=int(resource_section_id))
        if dialog_uuid:
            comments = comments.filter(Q(uuid=dialog_uuid.split(' ')[0]) |
                                       Q(dialog_uuid=dialog_uuid))
        if reply_uuid:
            comments = comments.filter(Q(uuid=reply_uuid) | Q(reply_comment__uuid=reply_uuid))
        if author_uuid:
            comments = comments.filter(author__uuid=author_uuid)
        if status:
            if int(status) in dict(Comment.STATUS_CHOICES):
                comments = comments.filter(status=int(status))
            else:
                comments = comments.filter(reduce(self._status_or, list(status)))
        if order_field:
            if (order_level.is_gt_lv1() and order_field in CommentService.COMMENT_PUBLIC_FIELD) \
                    or order_level.is_gt_lv10():
                if order == 'desc':
                    order_field = '-' + order_field
                comments = comments.order_by(order_field)
            else:
                raise ServiceError(code=400, message=ErrorMsg.ORDER_PARAMS_ERROR)
        if query:
            if query_field and query_level.is_gt_lv1():
                if query_field == 'content':
                    query_field = 'content__icontains'
                elif query_field == 'author':
                    query_field = 'author__nick__icontains'
                elif query_field == 'status':
                    query_field = 'status'
                elif query_level.is_lt_lv10():
                    raise ServiceError(code=403, message=ErrorMsg.QUERY_PERMISSION_DENIED)
                query_dict = {query_field: query}
                comments = comments.filter(**query_dict)
            elif query_level.is_gt_lv2():
                comments = comments.filter(Q(content__icontains=query) |
                                           Q(author__nick__icontains=query))
            else:
                raise ServiceError(code=403, message=ErrorMsg.QUERY_PERMISSION_DENIED)
        for comment in comments:
            if not self._has_get_permission(comment=comment):
                comments = comments.exclude(id=comment.id)
        comments, total = paging(comments, page=page, page_size=page_size)
        return 200, {'comments': [CommentService._comment_to_dict(comment=comment) for comment in comments],
                     'total': total}

    def create(self, resource_type, resource_uuid, reply_uuid=None,
               content=None, status=Comment.AUDIT):
        self.has_permission(PermissionName.COMMENT_CREATE)
        resource_type = CommentService.choices_format(resource_type, Comment.TYPE_CHOICES, None)
        resource, section = self._get_resource(resource_type, resource_uuid)
        dialog_uuid, reply_comment = self._get_reply(reply_uuid=reply_uuid, resource_uuid=resource_uuid)
        comment_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS,
                                      (resource_uuid + self.uuid + str(time.time())).encode('utf-8')))
        status = self._get_create_status(status=status, section=section)
        comment = Comment.objects.create(uuid=comment_uuid,
                                         resource_type=resource_type,
                                         resource_uuid=resource_uuid,
                                         resource_author_id=resource.author_id,
                                         resource_section=section,
                                         dialog_uuid=dialog_uuid,
                                         reply_comment=reply_comment,
                                         content=content,
                                         author_id=self.uid,
                                         status=status,
                                         last_editor_id=self.uid)
        return 201, CommentService._comment_to_dict(comment=comment)

    def update(self, comment_uuid, content=None, status=None,
               like_count=None, dislike_count=None):
        update_level, _ = self.get_permission_level(PermissionName.COMMENT_UPDATE)
        try:
            comment = Comment.objects.get(uuid=comment_uuid)
        except Comment.DoesNotExist:
            raise ServiceError(code=404, message=ContentErrorMsg.COMMENT_NOT_FOUND)
        if like_count or dislike_count:
            self._has_get_permission(comment=comment)
            # Todo comment like list
            pass
        is_self = comment.author_id == self.uid
        is_content_change = False
        edit_permission, set_role = False, None
        if comment.resource_section:
            set_role = SectionService.is_manager(user_uuid=self.uuid, section=comment.resource_section)
            edit_permission = SectionService.has_set_permission(
                permission=comment.resource_section.permission.comment_edit,
                set_role=set_role)
        if is_self and update_level.is_gt_lv1() or update_level.is_gt_lv10() or edit_permission:
            if content is not None and content != comment.content:
                comment.content, is_content_change = content, True
                comment.last_editor_id = self.uid
                comment.edit_at = timezone.now()
        elif not self._has_status_permission(comment=comment, set_role=set_role):
            raise ServiceError(code=403, message=ErrorMsg.PERMISSION_DENIED)
        if status and int(status) != comment.status:
            comment.status = self._get_update_status(status, comment, set_role, is_content_change)
        elif is_content_change:
            _, audit_level = self.get_permission_level(PermissionName.COMMENT_AUDIT, False)
            if comment.resource_section:
                audit_permission = SectionService.has_set_permission(
                    permission=comment.resource_section.permission.comment_audit,
                    set_role=set_role,
                    op=audit_level.is_gt_lv10())
            else:
                audit_permission = audit_level.is_gt_lv10()
            if not audit_permission and \
                (comment.status == Comment.ACTIVE or
                 comment.status == Comment.AUDIT or
                 comment.status == Comment.FAILED):
                comment.status = status if Setting().COMMENT_AUDIT else comment.status
        comment.save()
        return 200, CommentService._comment_to_dict(comment=comment)

    def delete(self, delete_id, force):
        if force:
            self.has_permission(PermissionName.COMMENT_DELETE)
        else:
            self.has_permission(PermissionName.COMMENT_CANCEL)
        result = {'id': delete_id}
        try:
            comment = Comment.objects.get(uuid=delete_id)
            result['name'], result['status'] = comment.content[:30] + '...', 'SUCCESS'
            if force:
                if self._has_delete_permission(comment=comment):
                    comment.delete()
                else:
                    raise ServiceError()
            else:
                if Setting().COMMENT_CANCEL and self._has_cancel_permission(comment=comment):
                    comment.status = Comment.CANCEL
                    comment.save()
                else:
                    raise ServiceError()
        except Comment.DoesNotExist:
            result['status'] = 'NOT_FOUND'
        except ServiceError:
            result['status'] = 'PERMISSION_DENIED'
        return result

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
                if SectionService.has_set_permission(permission=section.permission.comment_delete,
                                                     set_role=set_role):
                    return True
        elif comment.status == Comment.AUDIT or comment.status == Comment.FAILED:
            audit_level, _ = self.get_permission_level(PermissionName.COMMENT_AUDIT, False)
            if audit_level.is_gt_lv10():
                return True
            if section:
                set_role = SectionService.is_manager(user_uuid=self.uuid, section=section)
                if SectionService.has_set_permission(permission=section.permission.comment_audit,
                                                     set_role=set_role):
                    return True
        elif section and comment.status == Comment.RECYCLED:
            set_role = SectionService.is_manager(user_uuid=self.uuid, section=section)
            if SectionService.has_set_permission(permission=section.permission.comment_recycled,
                                                 set_role=set_role):
                return True
        return False

    def _has_delete_permission(self, comment):
        delete_level, _ = self.get_permission_level(PermissionName.COMMENT_DELETE, False)
        is_self = comment.author_id == self.uid
        if delete_level.is_gt_lv10() or is_self and delete_level.is_gt_lv1():
            return True
        if comment.resource_section:
            set_role = SectionService.is_manager(user_uuid=self.uuid, section=comment.resource_section)
            if SectionService.has_set_permission(permission=comment.resource_section.permission.comment_delete,
                                                 set_role=set_role):
                return True
        return False

    def _has_cancel_permission(self, comment):
        _, cancel_level = self.get_permission_level(PermissionName.COMMENT_CANCEL, False)
        is_self = comment.author_id == self.uid
        if cancel_level.is_gt_lv10() or is_self and cancel_level.is_gt_lv1():
            return True
        if comment.resource_section:
            set_role = SectionService.is_manager(user_uuid=self.uuid, section=comment.resource_section)
            if SectionService.has_set_permission(permission=comment.resource_section.permission.comment_cancel,
                                                 set_role=set_role):
                return True
        return False

    def _get_create_status(self, status, section):
        default = Comment.AUDIT if Setting().COMMENT_AUDIT else Comment.ACTIVE
        status = CommentService.choices_format(status, Comment.STATUS_CHOICES, default)
        if status == Comment.AUDIT:
            return default
        if status == Comment.ACTIVE or status == Comment.FAILED:
            if not Setting().COMMENT_AUDIT:
                return Comment.ACTIVE
            _, audit_level = self.get_permission_level(PermissionName.COMMENT_AUDIT, False)
            if audit_level.is_gt_lv10():
                return status
            if section:
                set_role = SectionService.is_manager(user_uuid=self.uuid, section=section)
                if SectionService.has_set_permission(permission=section.permission.comment_audit,
                                                     set_role=set_role):
                    return status
            raise ServiceError(code=403, message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
        if status == Comment.CANCEL:
            if Setting().COMMENT_CANCEL:
                _, cancel_level = self.get_permission_level(PermissionName.COMMENT_CANCEL, False)
                if cancel_level.is_gt_lv10():
                    return status
                if section:
                    set_role = SectionService.is_manager(user_uuid=self.uuid, section=section)
                    if SectionService.has_set_permission(permission=section.permission.comment_cancel,
                                                         set_role=set_role):
                        return status
            raise ServiceError(code=403, message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
        return status

    def _get_update_status(self, status, comment, set_role, is_content_change):
        default = comment.status
        section = comment.resource_section
        is_self = comment.author_id == self.uid
        status = CommentService.choices_format(status, Comment.STATUS_CHOICES, default)
        if status == comment.status and (status != Comment.ACTIVE and
                                         status != Comment.FAILED or
                                         (status == Comment.ACTIVE or
                                          status == Comment.FAILED) and
                                         not is_content_change):
            return status
        if status == Comment.ACTIVE or status == Comment.AUDIT or status == Comment.FAILED:
            if not Setting().COMMENT_AUDIT:
                return Comment.ACTIVE
            if is_content_change and status == Comment.AUDIT:
                return status
            _, audit_level = self.get_permission_level(PermissionName.COMMENT_AUDIT, False)
            if audit_level.is_gt_lv10():
                return status
            if section and SectionService.has_set_permission(permission=section.permission.comment_audit,
                                                             set_role=set_role):
                return status
            if is_self and is_content_change and status == Comment.ACTIVE:
                return Comment.AUDIT
            raise ServiceError(code=403, message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
        elif status == Comment.CANCEL:
            if Setting().COMMENT_CANCEL:
                _, cancel_level = self.get_permission_level(PermissionName.COMMENT_CANCEL, False)
                if cancel_level.is_gt_lv10() or is_self and cancel_level.is_gt_lv1() or section and \
                        SectionService.has_set_permission(permission=section.permission.comment_cancel,
                                                          set_role=set_role):
                    return status
        elif status == Comment.RECYCLED:
            if is_self or section and SectionService.has_set_permission(
                    permission=section.permission.comment_recycled,
                    set_role=set_role):
                return status
        raise ServiceError(code=403, message=ContentErrorMsg.STATUS_PERMISSION_DENIED)

    def _has_status_permission(self, comment, set_role):
        if comment.author_id == self.uid:
            return True
        _, audit_level = self.get_permission_level(PermissionName.COMMENT_AUDIT, False)
        _, cancel_level = self.get_permission_level(PermissionName.COMMENT_CANCEL, False)
        if audit_level.is_gt_lv10() or cancel_level.is_gt_lv10():
            return True
        if not comment.resource_section:
            return False
        if SectionService.has_set_permission(permission=comment.resource_section.permission.comment_audit,
                                             set_role=set_role) or \
                SectionService.has_set_permission(permission=comment.resource_section.permission.comment_cancel,
                                                  set_role=set_role):
            return True
        return False

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

    def _get_reply(self, reply_uuid, resource_uuid):
        dialog_uuid, reply_comment = None, None
        if reply_uuid:
            try:
                reply_comment = Comment.objects.get(uuid=reply_uuid, resource_uuid=resource_uuid)
                if reply_comment.author_id == self.uid:
                    raise ServiceError(message=ContentErrorMsg.COMMENT_REPLY_ERROR)
                if reply_comment.dialog_uuid and reply_comment.reply_comment.author_id == self.uid:
                    dialog_uuid = reply_comment.dialog_uuid
                else:
                    dialog_uuid = reply_uuid + ' ' + \
                                  str(uuid.uuid5(uuid.NAMESPACE_DNS,
                                                 (reply_uuid + self.uuid + str(time.time())).encode('utf-8')))
            except Comment.DoesNotExist:
                raise ServiceError(code=404, message=ContentErrorMsg.COMMENT_NOT_FOUND)
        return dialog_uuid, reply_comment

    @staticmethod
    def _comment_to_dict(comment, **kwargs):
        comment_dict = model_to_dict(comment)
        if comment.reply_comment:
            UserService.user_to_dict(comment.reply_comment.author, comment_dict, 'reply_user')
        UserService.user_to_dict(comment.author, comment_dict, 'author')
        UserService.user_to_dict(comment.last_editor, comment_dict, 'last_editor')
        for key in kwargs:
            comment_dict[key] = kwargs[key]
        return comment_dict
