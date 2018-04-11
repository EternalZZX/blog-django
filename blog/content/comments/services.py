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
from blog.content.articles.services import ArticleService, ArticleMetadataService
from blog.content.albums.models import Album
from blog.content.albums.services import AlbumService, AlbumMetadataService
from blog.content.photos.models import Photo
from blog.content.photos.services import PhotoService, PhotoMetadataService
from blog.common.base import Service, MetadataService
from blog.common.error import ServiceError
from blog.common.message import ErrorMsg, ContentErrorMsg
from blog.common.utils import paging, str_to_list, model_to_dict, get_md5
from blog.common.setting import Setting, PermissionName


class CommentService(Service):
    COMMENT_ORDER_FIELD = ['id', 'resource_type', 'resource_uuid', 'resource_author',
                           'resource_section', 'dialog_uuid', 'reply_comment',
                           'author', 'status', 'create_at', 'last_editor',
                           'edit_at', 'read_count', 'comment_count', 'like_count',
                           'dislike_count']
    METADATA_ORDER_FIELD = ['read_count', 'comment_count', 'like_count',
                            'dislike_count']

    def get(self, comment_uuid, like_list_type=None, like_list_start=0, like_list_end=10):
        self.has_permission(PermissionName.COMMENT_SELECT)
        try:
            comment = Comment.objects.get(uuid=comment_uuid)
            if not self._has_get_permission(comment=comment):
                raise Comment.DoesNotExist
        except Comment.DoesNotExist:
            raise ServiceError(code=404, message=ContentErrorMsg.COMMENT_NOT_FOUND)
        if like_list_type is None:
            operate_dict = {'read_count': CommentMetadataService.OPERATE_ADD} \
                if comment.status == Comment.ACTIVE else {}
            metadata = CommentMetadataService().update_metadata_count(resource=comment, **operate_dict)
            is_like_user = CommentMetadataService().is_like_user(resource=comment, user_id=self.uid)
            comment_dict = CommentService._comment_to_dict(comment=comment,
                                                           metadata=metadata,
                                                           is_like_user=is_like_user)
        else:
            like_level, _ = self.get_permission_level(PermissionName.COMMENT_LIKE)
            if like_level.is_gt_lv10() or like_level.is_gt_lv1() and \
                    int(like_list_type) == CommentMetadataService.LIKE_LIST:
                metadata, like_user_dict = CommentMetadataService().get_metadata_dict(
                    resource=comment, start=like_list_start, end=like_list_end, list_type=like_list_type)
                comment_dict = CommentService._comment_to_dict(comment=comment, metadata=metadata, **like_user_dict)
            else:
                raise ServiceError(code=403, message=ErrorMsg.PERMISSION_DENIED)
        return 200, comment_dict

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
                comments = comments.filter(reduce(self.status_or, list(status)))
        if order_field:
            if (order_level.is_gt_lv1() and order_field in CommentService.COMMENT_ORDER_FIELD) \
                    or order_level.is_gt_lv10():
                if order_field in CommentService.METADATA_ORDER_FIELD:
                    order_field = 'metadata__' + order_field
                if order == 'desc':
                    order_field = '-' + order_field
                comments = comments.order_by(order_field)
            else:
                raise ServiceError(code=400, message=ErrorMsg.ORDER_PARAMS_ERROR)
        if query:
            if query_field and query_level.is_gt_lv1():
                if query_field == 'uuid':
                    query_field = 'uuid'
                elif query_field == 'content':
                    query_field = 'content__icontains'
                elif query_field == 'author':
                    query_field = 'author__nick__icontains'
                elif query_field == 'status':
                    query_field = 'status'
                elif query_level.is_lt_lv10():
                    raise ServiceError(code=403, message=ErrorMsg.QUERY_PERMISSION_DENIED)
                comments = self.query_by_list(comments, [{query_field: item} for item in str_to_list(query)])
            elif query_level.is_gt_lv2():
                comments = comments.filter(Q(uuid=query) |
                                           Q(content__icontains=query) |
                                           Q(author__nick__icontains=query))
            else:
                raise ServiceError(code=403, message=ErrorMsg.QUERY_PERMISSION_DENIED)
        for comment in comments:
            if not self._has_get_permission(comment=comment):
                comments = comments.exclude(id=comment.id)
        comments, total = paging(comments, page=page, page_size=page_size)
        comment_dict_list = []
        for comment in comments:
            metadata = CommentMetadataService().get_metadata_count(resource=comment)
            comment_dict = CommentService._comment_to_dict(comment=comment, metadata=metadata)
            comment_dict_list.append(comment_dict)
        return 200, {'comments': comment_dict_list, 'total': total}

    def create(self, resource_type, resource_uuid, reply_uuid=None, content=None, status=Comment.AUDIT):
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
        self._update_comment_count(resource_type, status=status, resource=resource, reply_comment=reply_comment)
        return 201, CommentService._comment_to_dict(comment=comment)

    def update(self, comment_uuid, content=None, status=None, like_operate=None):
        update_level, _ = self.get_permission_level(PermissionName.COMMENT_UPDATE)
        try:
            comment = Comment.objects.get(uuid=comment_uuid)
        except Comment.DoesNotExist:
            raise ServiceError(code=404, message=ContentErrorMsg.COMMENT_NOT_FOUND)
        if like_operate is not None:
            metadata = self._update_like_list(comment=comment, operate=like_operate)
            return 200, CommentService._comment_to_dict(comment=comment, metadata=metadata)
        is_self = comment.author_id == self.uid
        is_content_change = False
        edit_permission, set_role = False, None
        if comment.resource_section:
            set_role = SectionService.is_manager(user_uuid=self.uuid, section=comment.resource_section)
            edit_permission = SectionService.has_set_permission(
                permission=comment.resource_section.permission.comment_edit,
                set_role=set_role)
        if is_self and update_level.is_gt_lv1() or update_level.is_gt_lv10() or edit_permission:
            if content is not None and get_md5(content) != get_md5(comment.content):
                comment.content, is_content_change = content, True
                comment.last_editor_id = self.uid
                comment.edit_at = timezone.now()
        elif not self._has_status_permission(comment=comment, set_role=set_role):
            raise ServiceError(code=403, message=ErrorMsg.PERMISSION_DENIED)
        status_old = comment.status
        if status and int(status) != status_old:
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
        self._update_comment_count(comment.resource_type, status=comment.status, status_old=status_old,
                                   resource_uuid=comment.resource_uuid, reply_comment=comment.reply_comment)
        metadata = CommentMetadataService().get_metadata_count(resource=comment)
        return 200, CommentService._comment_to_dict(comment=comment, metadata=metadata)

    def delete(self, delete_id, force):
        if force:
            self.has_permission(PermissionName.COMMENT_DELETE)
        else:
            self.has_permission(PermissionName.COMMENT_CANCEL)
        result = {'id': delete_id}
        try:
            comment = Comment.objects.get(uuid=delete_id)
            result['name'], result['status'] = comment.content[:30] + '...', 'SUCCESS'
            resource_type = comment.resource_type
            resource_uuid = comment.resource_uuid
            reply_comment = comment.reply_comment
            status_old = comment.status
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
            self._update_comment_count(resource_type, status_old=status_old,
                                       resource_uuid=resource_uuid, reply_comment=reply_comment)
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
            resource_type = int(resource_type)
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
        except (Article.DoesNotExist, Album.DoesNotExist, Photo.DoesNotExist):
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

    def _update_like_list(self, comment, operate):
        _, like_level = self.get_permission_level(PermissionName.COMMENT_LIKE)
        if like_level.is_lt_lv1():
            raise ServiceError(code=403, message=ErrorMsg.PERMISSION_DENIED)
        _, read_permission = self._has_get_permission(comment=comment)
        if not read_permission:
            raise ServiceError(code=403, message=ErrorMsg.PERMISSION_DENIED)
        return CommentMetadataService().update_like_list(resource=comment, user_id=self.uid, operate=operate)

    def _update_comment_count(self, resource_type, status=None, status_old=None,
                              resource_uuid=None, resource=None, reply_comment=None):
        if status == Comment.ACTIVE and status_old != Comment.ACTIVE:
            operate = MetadataService.OPERATE_ADD
        elif status != Comment.ACTIVE and status_old == Comment.ACTIVE:
            operate = MetadataService.OPERATE_MINUS
        else:
            return
        if not resource:
            resource, _ = self._get_resource(resource_type, resource_uuid)
        if resource_type == Comment.ARTICLE:
            ArticleMetadataService().update_metadata_count(resource, comment_count=operate)
        elif resource_type == Comment.ALBUM:
            AlbumMetadataService().update_metadata_count(resource, comment_count=operate)
        elif resource_type == Comment.PHOTO:
            PhotoMetadataService().update_metadata_count(resource, comment_count=operate)
        if reply_comment:
            CommentMetadataService().update_metadata_count(reply_comment, comment_count=operate)

    @staticmethod
    def _comment_to_dict(comment, metadata=None, **kwargs):
        comment_dict = model_to_dict(comment)
        if comment.reply_comment:
            UserService.user_to_dict(comment.reply_comment.author, comment_dict, 'reply_user')
        UserService.user_to_dict(comment.author, comment_dict, 'author')
        UserService.user_to_dict(comment.last_editor, comment_dict, 'last_editor')
        comment_dict['metadata'] = {}
        comment_dict['metadata']['read_count'] = metadata.read_count if metadata else 0
        comment_dict['metadata']['comment_count'] = metadata.comment_count if metadata else 0
        comment_dict['metadata']['like_count'] = metadata.like_count if metadata else 0
        comment_dict['metadata']['dislike_count'] = metadata.dislike_count if metadata else 0
        for key in kwargs:
            comment_dict[key] = kwargs[key]
        return comment_dict


class CommentMetadataService(MetadataService):
    METADATA_KEY = 'COMMENT_METADATA'
    LIKE_LIST_KEY = 'COMMENT_LIKE_LIST'
    DISLIKE_LIST_KEY = 'COMMENT_DISLIKE_LIST'

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
            comment = Comment.objects.get(uuid=resource_uuid)
            self._set_resource_sql_metadata(comment, metadata, like_list_key, dislike_list_key)
        except Comment.DoesNotExist:
            self.redis_client.hash_delete(self.METADATA_KEY, resource_uuid)
            self.redis_client.delete(like_list_key, dislike_list_key)
