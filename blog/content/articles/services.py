#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid
import time

from functools import reduce

from django.db.models import Q
from django.utils import timezone
from django.core.files.base import ContentFile

from blog.account.users.services import UserService
from blog.content.sections.models import Section
from blog.content.sections.services import SectionService
from blog.content.articles.models import Article
from blog.content.albums.models import Album
from blog.content.photos.models import Photo
from blog.common.base import Service, MetadataService
from blog.common.error import ServiceError
from blog.common.message import ErrorMsg, ContentErrorMsg
from blog.common.utils import paging, str_to_list, model_to_dict, html_to_str, get_md5
from blog.common.setting import Setting, PermissionName, AuthType


class ArticleService(Service):
    ARTICLE_ORDER_FIELD = ['id', 'title', 'overview', 'author', 'section',
                           'status', 'privacy', 'read_level', 'create_at',
                           'last_editor', 'edit_at', 'read_count',
                           'comment_count', 'like_count', 'dislike_count']
    METADATA_ORDER_FIELD = ['read_count', 'comment_count', 'like_count',
                            'dislike_count']

    def __init__(self, request=None, instance=None, auth_type=AuthType.HEADER, token=None):
        super(ArticleService, self).__init__(request=request, instance=instance,
                                             auth_type=auth_type, token=token)
        self.section_service = SectionService(instance=self)

    def get(self, article_uuid, like_list_type=None, like_list_start=0, like_list_end=10):
        self.has_permission(PermissionName.ARTICLE_SELECT)
        try:
            article = Article.objects.get(uuid=article_uuid)
            get_permission, read_permission = self.has_get_permission(article=article)
            if not get_permission:
                raise Article.DoesNotExist
            if not read_permission:
                raise ServiceError(code=403, message=ErrorMsg.PERMISSION_DENIED)
        except Article.DoesNotExist:
            raise ServiceError(code=404, message=ContentErrorMsg.ARTICLE_NOT_FOUND)
        is_like_user = ArticleMetadataService().is_like_user(resource=article, user_id=self.uid)
        like_user_dict = {}
        if like_list_type is None:
            operate_dict = {'read_count': ArticleMetadataService.OPERATE_ADD} \
                if article.status == Article.ACTIVE else {}
            metadata = ArticleMetadataService().update_metadata_count(resource=article, **operate_dict)
        else:
            like_level, _ = self.get_permission_level(PermissionName.ARTICLE_LIKE)
            if like_level.is_gt_lv10() or like_level.is_gt_lv1() and \
                    int(like_list_type) == ArticleMetadataService.LIKE_LIST:
                metadata, like_user_dict = ArticleMetadataService().get_metadata_dict(
                    resource=article, start=like_list_start, end=like_list_end, list_type=like_list_type)
            else:
                raise ServiceError(code=403, message=ErrorMsg.PERMISSION_DENIED)
        article_dict = ArticleService._article_to_dict(article=article,
                                                       metadata=metadata,
                                                       is_like_user=is_like_user,
                                                       **like_user_dict)
        return 200, article_dict

    def list(self, page=0, page_size=10, section_name=None, author_uuid=None,
             status=None, order_field=None, order='desc', query=None,
             query_field=None):
        query_level, order_level = self.get_permission_level(PermissionName.ARTICLE_SELECT)
        articles = Article.objects.all()
        if section_name:
            articles = articles.filter(section__name=section_name)
        if author_uuid:
            articles = articles.filter(author__uuid=author_uuid)
        if status:
            if int(status) in dict(Article.STATUS_CHOICES):
                articles = articles.filter(status=int(status))
            else:
                articles = articles.filter(reduce(self.status_or, list(status)))
        if order_field:
            if (order_level.is_gt_lv1() and order_field in ArticleService.ARTICLE_ORDER_FIELD) \
                    or order_level.is_gt_lv10():
                if order_field in ArticleService.METADATA_ORDER_FIELD:
                    order_field = 'metadata__' + order_field
                if order == 'desc':
                    order_field = '-' + order_field
                articles = articles.order_by(order_field)
            else:
                raise ServiceError(code=400, message=ErrorMsg.ORDER_PARAMS_ERROR)
        if query:
            if query_field and query_level.is_gt_lv1():
                if query_field == 'uuid':
                    query_field = 'uuid'
                elif query_field == 'title':
                    query_field = 'title__icontains'
                elif query_field == 'keywords':
                    query_field = 'keywords__icontains'
                elif query_field == 'content':
                    query_field = 'content__search'
                elif query_field == 'author':
                    query_field = 'author__nick__icontains'
                elif query_field == 'section':
                    query_field = 'section__nick__icontains'
                elif query_field == 'status':
                    query_field = 'status'
                elif query_level.is_lt_lv10():
                    raise ServiceError(code=403, message=ErrorMsg.QUERY_PERMISSION_DENIED)
                articles = self.query_by_list(articles, [{query_field: item} for item in str_to_list(query)])
            elif query_level.is_gt_lv2():
                articles = articles.filter(Q(uuid=query) |
                                           Q(title__icontains=query) |
                                           Q(keywords__icontains=query) |
                                           Q(content__search=query) |
                                           Q(author__nick__icontains=query) |
                                           Q(section__nick__icontains=query))
            else:
                raise ServiceError(code=403, message=ErrorMsg.QUERY_PERMISSION_DENIED)
        # Todo fix performance issue
        article_read_list = {}
        for article in articles:
            get_permission, read_permission = self.has_get_permission(article=article)
            if not get_permission:
                articles = articles.exclude(id=article.id)
            else:
                article_read_list[article.id] = read_permission
        articles, total = paging(articles, page=page, page_size=page_size)
        article_dict_list = []
        for article in articles:
            metadata = ArticleMetadataService().get_metadata_count(resource=article)
            is_like_user = ArticleMetadataService().is_like_user(resource=article, user_id=self.uid)
            article_dict = ArticleService._article_to_dict(article=article,
                                                           metadata=metadata,
                                                           content=False,
                                                           is_like_user=is_like_user,
                                                           read_permission=article_read_list[article.id])
            article_dict_list.append(article_dict)
        return 200, {'articles': article_dict_list, 'total': total}

    def create(self, title, keywords=None, cover_uuid=None, overview=None,
               content=None, section_name=None, status=Article.AUDIT,
               privacy=Article.PUBLIC, read_level=100, file_storage=False):
        self.has_permission(PermissionName.ARTICLE_CREATE)
        article_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, ('%s%s%s' % (title, self.uuid, time.time())).encode('utf-8')))
        keyword_str = ''
        for keyword in keywords:
            keyword_str = keyword_str + keyword + ','
        keyword_str = keyword_str[:-1] if keyword_str else keyword_str
        cover = self._get_cover_url(user_id=self.uid, cover_uuid=cover_uuid)
        if not overview and content:
            overview = html_to_str(content[:200])
            if len(content) > 200:
                overview = overview + '...'
        section = self._get_section(section_name=section_name)
        status = self._get_create_status(status=status, section=section)
        privacy = self._get_privacy(privacy=privacy)
        read_level = self._get_read_level(read_level=read_level)
        content_file = None
        if file_storage:
            content_file = ContentFile(content, article_uuid + '.data')
            content = None
        article = Article.objects.create(uuid=article_uuid,
                                         title=title,
                                         keywords=keyword_str,
                                         cover=cover,
                                         overview=overview,
                                         content=content,
                                         content_file=content_file,
                                         author_id=self.uid,
                                         section=section,
                                         status=status,
                                         privacy=privacy,
                                         read_level=read_level,
                                         last_editor_id=self.uid)
        return 201, ArticleService._article_to_dict(article=article)

    def update(self, article_uuid, title=None, keywords=None, cover_uuid=None,
               overview=None, content=None, section_name=None, status=None,
               privacy=None, read_level=None, like_operate=None):
        update_level, _ = self.get_permission_level(PermissionName.ARTICLE_UPDATE)
        try:
            article = Article.objects.get(uuid=article_uuid)
        except Article.DoesNotExist:
            raise ServiceError(code=404,
                               message=ContentErrorMsg.ARTICLE_NOT_FOUND)
        if like_operate is not None:
            metadata = self._update_like_list(article=article, operate=like_operate)
            is_like_user = ArticleMetadataService().is_like_user(resource=article, user_id=self.uid)
            return 200, ArticleService._article_to_dict(article=article,
                                                        metadata=metadata,
                                                        is_like_user=is_like_user)
        is_self = article.author_id == self.uid
        is_content_change, is_edit = False, False
        set_role = SectionService.is_manager(user_uuid=self.uuid, section=article.section)
        edit_permission = SectionService.has_set_permission(
            permission=article.section.permission.article_edit,
            set_role=set_role,
            op=update_level.is_gt_lv10())
        if is_self and update_level.is_gt_lv1() or edit_permission:
            if title and title != article.title:
                article.title, is_content_change = title, True
            if keywords is not None:
                keyword_str = ''
                for keyword in keywords:
                    keyword_str = keyword_str + keyword + ','
                keyword_str = keyword_str[:-1] if keyword_str else keyword_str
                if keyword_str != article.keywords:
                    article.keywords, is_content_change = keyword_str, True
            if cover_uuid is not None:
                article.cover = self._get_cover_url(user_id=self.uid, cover_uuid=cover_uuid)
            if overview is not None and get_md5(overview) != get_md5(article.overview):
                article.overview, is_content_change = overview, True
            if content is not None and self._update_content(article=article, content=content):
                is_content_change = True
            if section_name is not None and (not article.section or section_name != article.section.name):
                section = self._get_section(section_name=section_name)
                article.section, is_content_change = section, True
                set_role = SectionService.is_manager(user_uuid=self.uuid, section=section)
            if privacy is not None and int(privacy) != article.privacy:
                article.privacy, is_edit = self._get_privacy(privacy=privacy), True
            if read_level is not None and int(read_level) != article.read_level:
                article.read_level, is_edit = self._get_read_level(read_level=read_level), True
            if is_content_change or is_edit:
                article.last_editor_id = self.uid
                article.edit_at = timezone.now()
        elif not self._has_status_permission(article=article, set_role=set_role):
            raise ServiceError(code=403, message=ErrorMsg.PERMISSION_DENIED)
        if status is not None and int(status) != article.status:
            article.status = self._get_update_status(status, article, set_role, is_content_change)
        elif is_content_change:
            _, audit_level = self.get_permission_level(PermissionName.ARTICLE_AUDIT, False)
            audit_permission = SectionService.has_set_permission(
                permission=article.section.permission.article_audit,
                set_role=set_role,
                op=audit_level.is_gt_lv10())
            if not audit_permission and \
                (article.status == Article.ACTIVE or
                 article.status == Article.AUDIT or
                 article.status == Article.FAILED):
                article.status = status if Setting().ARTICLE_AUDIT else article.status
        article.save()
        metadata = ArticleMetadataService().get_metadata_count(resource=article)
        is_like_user = ArticleMetadataService().is_like_user(resource=article, user_id=self.uid)
        return 200, ArticleService._article_to_dict(article=article,
                                                    metadata=metadata,
                                                    is_like_user=is_like_user)

    def delete(self, delete_id, force):
        if force:
            self.has_permission(PermissionName.ARTICLE_DELETE)
        else:
            self.has_permission(PermissionName.ARTICLE_CANCEL)
        result = {'id': delete_id}
        try:
            article = Article.objects.get(uuid=delete_id)
            result['name'], result['status'] = article.title, 'SUCCESS'
            if force:
                if self._has_delete_permission(article=article):
                    article.delete()
                else:
                    raise ServiceError()
            else:
                if Setting().ARTICLE_CANCEL and self._has_cancel_permission(article=article):
                    article.status = Article.CANCEL
                    article.save()
                else:
                    raise ServiceError()
        except Article.DoesNotExist:
            result['status'] = 'NOT_FOUND'
        except ServiceError:
            result['status'] = 'PERMISSION_DENIED'
        return result

    def has_get_permission(self, article):
        section = article.section
        is_author = article.author_id == self.uid
        if is_author and article.status != Article.CANCEL:
            return True, True
        permission_level, _ = self.get_permission_level(PermissionName.ARTICLE_PERMISSION, False)
        if permission_level.is_gt_lv10():
            return True, True
        if not section:
            return False, False
        _, read_permission = self.section_service.has_get_permission(article.section)
        if not read_permission:
            return False, False
        if article.status == Article.ACTIVE:
            privacy_level, _ = self.get_permission_level(PermissionName.ARTICLE_PRIVACY, False)
            read_permission_level, _ = self.get_permission_level(PermissionName.ARTICLE_READ, False)
            read_level = self.get_permission_value(PermissionName.READ_LEVEL, False)
            if (article.privacy == Article.PUBLIC or privacy_level.is_gt_lv10()) and \
                    (read_level >= article.read_level or read_permission_level.is_gt_lv10()):
                return True, True
            set_role = SectionService.is_manager(user_uuid=self.uuid, section=section)
            if SectionService.has_set_permission(
                    permission=section.permission.article_audit,
                    set_role=set_role):
                return True, True
            return article.privacy != Article.PRIVATE, False
        elif article.status == Article.CANCEL:
            cancel_level, _ = self.get_permission_level(PermissionName.ARTICLE_CANCEL, False)
            if cancel_level.is_gt_lv10():
                return True, True
            set_role = SectionService.is_manager(user_uuid=self.uuid, section=section)
            if SectionService.has_set_permission(
                    permission=section.permission.article_delete,
                    set_role=set_role):
                return True, True
        elif article.status == Article.AUDIT or article.status == Article.FAILED:
            audit_level, _ = self.get_permission_level(PermissionName.ARTICLE_AUDIT, False)
            if audit_level.is_gt_lv10():
                return True, True
            set_role = SectionService.is_manager(user_uuid=self.uuid, section=section)
            if SectionService.has_set_permission(
                    permission=section.permission.article_audit,
                    set_role=set_role):
                return True, True
        elif article.status == Article.DRAFT:
            set_role = SectionService.is_manager(user_uuid=self.uuid, section=section)
            if SectionService.has_set_permission(
                    permission=section.permission.article_draft,
                    set_role=set_role):
                return True, True
        elif article.status == Article.RECYCLED:
            set_role = SectionService.is_manager(user_uuid=self.uuid, section=section)
            if SectionService.has_set_permission(
                    permission=section.permission.article_recycled,
                    set_role=set_role):
                return True, True
        return False, False

    def _has_delete_permission(self, article):
        delete_level, _ = self.get_permission_level(PermissionName.ARTICLE_DELETE, False)
        is_self = article.author_id == self.uid
        if delete_level.is_gt_lv10() or is_self and delete_level.is_gt_lv1():
            return True
        set_role = SectionService.is_manager(user_uuid=self.uuid, section=article.section)
        if SectionService.has_set_permission(
                permission=article.section.permission.article_delete,
                set_role=set_role):
            return True
        return False

    def _has_cancel_permission(self, article):
        _, cancel_level = self.get_permission_level(PermissionName.ARTICLE_CANCEL, False)
        is_self = article.author_id == self.uid
        if cancel_level.is_gt_lv10() or is_self and cancel_level.is_gt_lv1():
            return True
        set_role = SectionService.is_manager(user_uuid=self.uuid, section=article.section)
        if SectionService.has_set_permission(
                permission=article.section.permission.article_cancel,
                set_role=set_role):
            return True
        return False

    def _get_section(self, section_name):
        section = None
        if section_name:
            try:
                section = Section.objects.get(name=section_name)
                get_permission, read_permission = self.section_service.has_get_permission(section)
                if not get_permission:
                    raise ServiceError(code=400, message=ContentErrorMsg.SECTION_NOT_FOUND)
                if not read_permission:
                    raise ServiceError(code=403, message=ContentErrorMsg.SECTION_PERMISSION_DENIED)
                section_policy = section.policy
                if section_policy.article_mute:
                    raise ServiceError(code=403, message=ContentErrorMsg.SECTION_PERMISSION_DENIED)
                if section_policy.max_articles is not None and \
                        Article.objects.filter(author_id=self.uid,
                                               section__name=section_name).count() >= section_policy.max_articles:
                    raise ServiceError(code=403, message=ContentErrorMsg.SECTION_PERMISSION_DENIED)
                start = timezone.now().date()
                end = start + timezone.timedelta(days=1)
                if section_policy.max_articles_one_day is not None and \
                        Article.objects.filter(author_id=self.uid,
                                               section__name=section_name,
                                               create_at__range=(start, end)).count() >= \
                        section_policy.max_articles_one_day:
                    raise ServiceError(code=403, message=ContentErrorMsg.SECTION_PERMISSION_DENIED)
            except Section.DoesNotExist:
                raise ServiceError(code=400,
                                   message=ContentErrorMsg.SECTION_NOT_FOUND)
        return section

    def _get_create_status(self, status, section):
        default = Article.AUDIT if Setting().ARTICLE_AUDIT else Article.ACTIVE
        status = ArticleService.choices_format(status, Article.STATUS_CHOICES, default)
        if status == Article.AUDIT:
            return default if section else Article.ACTIVE
        if status == Article.ACTIVE or status == Article.FAILED:
            if not section or not Setting().ARTICLE_AUDIT:
                return Article.ACTIVE
            _, audit_level = self.get_permission_level(PermissionName.ARTICLE_AUDIT, False)
            set_role = SectionService.is_manager(user_uuid=self.uuid, section=section)
            if SectionService.has_set_permission(permission=section.permission.article_audit,
                                                 set_role=set_role,
                                                 op=audit_level.is_gt_lv10()):
                return status
            raise ServiceError(code=403, message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
        if status == Article.CANCEL:
            if section and Setting().ARTICLE_CANCEL:
                _, cancel_level = self.get_permission_level(PermissionName.ARTICLE_CANCEL, False)
                set_role = SectionService.is_manager(user_uuid=self.uuid, section=section)
                if SectionService.has_set_permission(permission=section.permission.article_cancel,
                                                     set_role=set_role,
                                                     op=cancel_level.is_gt_lv10()):
                    return status
            raise ServiceError(code=403, message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
        return status

    def _get_update_status(self, status, article, set_role, is_content_change):
        default = article.status
        section = article.section
        is_self = article.author_id == self.uid
        status = ArticleService.choices_format(status, Article.STATUS_CHOICES, default)
        if status == article.status and (status != Article.ACTIVE and
                                         status != Article.FAILED or
                                         (status == Article.ACTIVE or
                                          status == Article.FAILED) and
                                         not is_content_change):
            return status
        if status == Article.ACTIVE or status == Article.AUDIT or status == Article.FAILED:
            if not section or not Setting().ARTICLE_AUDIT:
                return Article.ACTIVE
            if is_content_change and status == Article.AUDIT:
                return status
            _, audit_level = self.get_permission_level(PermissionName.ARTICLE_AUDIT, False)
            if SectionService.has_set_permission(permission=section.permission.article_audit,
                                                 set_role=set_role,
                                                 op=audit_level.is_gt_lv10()):
                return status
            if is_self and is_content_change and status == Article.ACTIVE:
                return Article.AUDIT
            raise ServiceError(code=403, message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
        elif status == Article.CANCEL:
            if Setting().ARTICLE_CANCEL:
                _, cancel_level = self.get_permission_level(PermissionName.ARTICLE_CANCEL, False)
                if cancel_level.is_gt_lv10() or is_self and cancel_level.is_gt_lv1() or section and \
                        SectionService.has_set_permission(permission=section.permission.article_cancel,
                                                          set_role=set_role):
                    return status
        elif status == Article.DRAFT:
            if is_self or section and SectionService.has_set_permission(
                    permission=section.permission.article_draft,
                    set_role=set_role):
                return status
        elif status == Article.RECYCLED:
            if is_self or section and SectionService.has_set_permission(
                    permission=section.permission.article_recycled,
                    set_role=set_role):
                return status
        raise ServiceError(code=403, message=ContentErrorMsg.STATUS_PERMISSION_DENIED)

    def _has_status_permission(self, article, set_role):
        if article.author_id == self.uid:
            return True
        _, audit_level = self.get_permission_level(PermissionName.COMMENT_AUDIT, False)
        _, cancel_level = self.get_permission_level(PermissionName.COMMENT_CANCEL, False)
        if audit_level.is_gt_lv10() or cancel_level.is_gt_lv10():
            return True
        if not article.section:
            return False
        if SectionService.has_set_permission(article.section.permission.comment_audit, set_role) or \
                SectionService.has_set_permission(article.section.permission.comment_cancel, set_role) or \
                SectionService.has_set_permission(article.section.permission.article_draft, set_role) or \
                SectionService.has_set_permission(article.section.permission.article_recycled, set_role):
            return True
        return False

    @staticmethod
    def _update_content(article, content):
        if article.content_file:
            content_old = article.content_file.read()
            article.content_file.seek(0)
            if get_md5(content_old) != get_md5(content):
                with open(article.content_file.path, 'w') as content_file:
                    content_file.write(content)
                return True
        else:
            content_old = article.content
            if get_md5(content_old) != get_md5(content):
                article.content = content
                return True
        return False

    def _update_like_list(self, article, operate):
        _, like_level = self.get_permission_level(PermissionName.ARTICLE_LIKE)
        if like_level.is_lt_lv1():
            raise ServiceError(code=403, message=ErrorMsg.PERMISSION_DENIED)
        _, read_permission = self.has_get_permission(article=article)
        if not read_permission:
            raise ServiceError(code=403, message=ErrorMsg.PERMISSION_DENIED)
        return ArticleMetadataService().update_like_list(resource=article, user_id=self.uid, operate=operate)

    def _get_privacy(self, privacy=Article.PUBLIC):
        _, privacy_level = self.get_permission_level(PermissionName.ARTICLE_PRIVACY, False)
        privacy = ArticleService.choices_format(privacy, Article.PRIVACY_CHOICES, Article.PUBLIC)
        if privacy == Article.PROTECTED and privacy_level.is_lt_lv1() or \
                privacy == Article.PRIVATE and privacy_level.is_lt_lv2():
            privacy = Article.PUBLIC
        return privacy

    def _get_read_level(self, read_level=100):
        _, read_permission_level = self.get_permission_level(PermissionName.ARTICLE_READ, False)
        read_level = int(read_level) if read_level else 100
        if read_permission_level.is_lt_lv1():
            read_level = 100
        else:
            self_read_level = self.get_permission_value(PermissionName.READ_LEVEL, False)
            if read_level > self_read_level and read_permission_level.is_lt_lv10():
                read_level = self_read_level
        return read_level

    @staticmethod
    def _get_cover_url(user_id, cover_uuid):
        if not cover_uuid:
            return None
        try:
            photo = Photo.objects.get(Q(uuid=cover_uuid,
                                        author__id=user_id,
                                        privacy=Photo.PUBLIC) |
                                      Q(uuid=cover_uuid,
                                        album__system=Album.ARTICLE_COVER_ALBUM,
                                        privacy=Photo.PUBLIC))
            if Setting().PHOTO_THUMBNAIL and photo.image_middle:
                return photo.image_middle.url
            else:
                return photo.image_large.url
        except Photo.DoesNotExist:
            return None

    @staticmethod
    def _article_to_dict(article, metadata=None, content=True, **kwargs):
        article_dict = model_to_dict(article)
        if not content:
            del article_dict['content']
        elif article.content_file:
            article_dict['content'] = article.content_file.read()
        UserService.dict_add_user(article.author, article_dict, 'author')
        UserService.dict_add_user(article.last_editor, article_dict, 'last_editor')
        if article.section:
            article_dict['section'] = {
                'name': article.section.name,
                'nick': article.section.nick
            }
        article_dict['metadata'] = {}
        article_dict['metadata']['read_count'] = metadata.read_count if metadata else 0
        article_dict['metadata']['comment_count'] = metadata.comment_count if metadata else 0
        article_dict['metadata']['like_count'] = metadata.like_count if metadata else 0
        article_dict['metadata']['dislike_count'] = metadata.dislike_count if metadata else 0
        for key in kwargs:
            article_dict[key] = kwargs[key]
        return article_dict


class ArticleMetadataService(MetadataService):
    METADATA_KEY = 'ARTICLE_METADATA'
    LIKE_LIST_KEY = 'ARTICLE_LIKE_LIST'
    DISLIKE_LIST_KEY = 'ARTICLE_DISLIKE_LIST'

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
            article = Article.objects.get(uuid=resource_uuid)
            self._set_resource_sql_metadata(article, metadata, like_list_key, dislike_list_key)
        except Article.DoesNotExist:
            self.redis_client.hash_delete(self.METADATA_KEY, resource_uuid)
            self.redis_client.delete(like_list_key, dislike_list_key)
