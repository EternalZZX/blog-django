#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid
import time

from functools import reduce

from django.db.models import Q
from django.utils.timezone import now, timedelta

from blog.account.users.services import UserService
from blog.content.sections.models import Section
from blog.content.sections.services import SectionService
from blog.content.articles.models import Article
from blog.common.base import Service
from blog.common.error import ServiceError
from blog.common.message import ErrorMsg, ContentErrorMsg
from blog.common.utils import paging, model_to_dict, html_to_str
from blog.common.setting import Setting, PermissionName


class ArticleService(Service):
    ARTICLE_PUBLIC_FIELD = ['id', 'uuid', 'title', 'keywords', 'overview',
                            'author', 'section', 'status', 'privacy',
                            'read_level', 'like_count', 'dislike_count',
                            'create_at', 'last_editor', 'edit_at']

    def __init__(self, request):
        super(ArticleService, self).__init__(request=request)
        self.section_service = SectionService(request=request)

    def get(self, article_uuid):
        self.has_permission(PermissionName.ARTICLE_SELECT)
        try:
            article = Article.objects.get(uuid=article_uuid)
            get_permission, read_permission = self._has_get_permission(article=article)
            if not get_permission:
                raise Article.DoesNotExist
            article_dict = ArticleService._article_to_dict(article=article)
        except Article.DoesNotExist:
            raise ServiceError(code=404,
                               message=ContentErrorMsg.ARTICLE_NOT_FOUND)
        return 200, article_dict

    def list(self, page=0, page_size=10, section_id=None, author_uuid=None,
             status=None, order_field=None, order='desc', query=None,
             query_field=None):
        query_level, order_level = self.get_permission_level(PermissionName.ARTICLE_SELECT)
        articles = Article.objects.all()
        if section_id:
            articles = articles.filter(section_id=section_id)
        if author_uuid:
            articles = articles.filter(author__uuid=author_uuid)
        if status:
            if int(status) in dict(Article.STATUS_CHOICES):
                articles = articles.filter(status=int(status))
            else:
                articles = articles.filter(reduce(self._status_or, list(status)))
        if order_field:
            if (order_level.is_gt_lv1() and order_field in ArticleService.ARTICLE_PUBLIC_FIELD) \
                    or order_level.is_gt_lv10():
                if order == 'desc':
                    order_field = '-' + order_field
                articles = articles.order_by(order_field)
            else:
                raise ServiceError(code=400,
                                   message=ErrorMsg.ORDER_PARAMS_ERROR)
        if query:
            if query_field and query_level.is_gt_lv1():
                if query_field == 'title':
                    query_field = 'title__icontains'
                elif query_field == 'keywords':
                    query_field = 'keywords__icontains'
                elif query_field == 'content':
                    query_field = 'content__icontains'
                elif query_field == 'author':
                    query_field = 'author__nick__icontains'
                elif query_field == 'section':
                    query_field = 'section__nick__icontains'
                elif query_field == 'status':
                    query_field = 'status'
                elif query_level.is_lt_lv10():
                    raise ServiceError(code=403,
                                       message=ErrorMsg.QUERY_PERMISSION_DENIED)
                query_dict = {query_field: query}
                articles = articles.filter(**query_dict)
            elif query_level.is_gt_lv2():
                articles = articles.filter(Q(title__icontains=query) |
                                           Q(keywords__icontains=query) |
                                           Q(content__icontains=query) |
                                           Q(author__nick__icontains=query) |
                                           Q(section__nick__icontains=query))
            else:
                raise ServiceError(code=403,
                                   message=ErrorMsg.QUERY_PERMISSION_DENIED)
        article_read_list = {}
        for article in articles:
            get_permission, read_permission = self._has_get_permission(article=article)
            if not get_permission:
                articles = articles.exclude(id=article.id)
            else:
                article_read_list[article.id] = read_permission
        articles, total = paging(articles, page=page, page_size=page_size)
        article_dict_list = []
        for article in articles:
            article_dict = ArticleService._article_to_dict(
                article=article,
                read_permission=article_read_list[article.id])
            del article_dict['content']
            del article_dict['content_url']
            article_dict_list.append(article_dict)
        return 200, {'articles': article_dict_list, 'total': total}

    def create(self, title, keywords=None, overview=None, content=None,
               section_id=None, status=Article.AUDIT, privacy=Article.PUBLIC,
               read_level=100):
        self.has_permission(PermissionName.ARTICLE_CREATE)
        article_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, (title + self.uuid + str(time.time())).encode('utf-8')))
        keyword_str = ''
        for keyword in keywords:
            keyword_str = keyword_str + keyword + ';'
        keyword_str = keyword_str[:-1] if keyword_str else keyword_str
        if not overview and content:
            overview = html_to_str(content[:200])
            if len(content) > 200:
                overview = overview + '...'
        section = self._get_section(section_id=section_id)
        status = self._get_create_status(status=status, section=section)
        privacy = self._get_privacy(privacy=privacy)
        read_level = self._get_read_level(read_level=read_level)
        article = Article.objects.create(uuid=article_uuid,
                                         title=title,
                                         keywords=keyword_str,
                                         overview=overview,
                                         content=content,
                                         author_id=self.uid,
                                         section=section,
                                         status=status,
                                         privacy=privacy,
                                         read_level=read_level,
                                         last_editor_id=self.uid)
        return 201, ArticleService._article_to_dict(article=article)

    def update(self, article_uuid, title, keywords=None, overview=None,
               content=None, section_id=None, status=Article.AUDIT,
               privacy=Article.PUBLIC, read_level=100, like_count=None,
               dislike_count=None):
        update_level, _ = self.get_permission_level(PermissionName.ARTICLE_UPDATE)
        try:
            article = Article.objects.get(uuid=article_uuid)
        except Article.DoesNotExist:
            raise ServiceError(code=404,
                               message=ContentErrorMsg.ARTICLE_NOT_FOUND)
        if like_count or dislike_count:
            _, read_permission = self._has_get_permission(article=article)
            #Todo article like list
            pass
        is_self = article.author_id == self.uid
        is_content_change, is_edit = False, False
        set_role = self.section_service.is_manager(section=article.section)
        edit_permission = self.section_service.has_set_permission(
            permission=article.section.sectionpermission.article_edit,
            set_role=set_role,
            op=update_level.is_gt_lv10())
        if is_self or edit_permission:
            if title and title != article.title:
                article.title, is_content_change = title, True
            if keywords is not None:
                keyword_str = ''
                for keyword in keywords:
                    keyword_str = keyword_str + keyword + ';'
                keyword_str = keyword_str[:-1] if keyword_str else keyword_str
                if keyword_str != article.keywords:
                    article.keywords, is_content_change = keyword_str, True
            if overview is not None and overview != article.overview:
                article.overview, is_content_change = overview, True
            if content is not None and content != article.content:
                article.content, is_content_change = content, True
            if section_id is not None and int(section_id) != int(article.section_id):
                section = self._get_section(section_id=section_id)
                article.section, is_content_change = section, True
                set_role = self.section_service.is_manager(section=section)
            if privacy and int(privacy) != article.privacy:
                article.privacy, is_edit = self._get_privacy(privacy=privacy), True
            if read_level and int(read_level) != article.read_level:
                article.read_level, is_edit = self._get_read_level(read_level=read_level), True
        else:
            raise ServiceError(code=403, message=ErrorMsg.PERMISSION_DENIED)
        if is_content_change or is_edit:
            article.last_editor_id = self.uid
            article.edit_at = now().date()
        if status and int(status) != article.status:
            article.status = self._get_update_status(status, article, set_role, is_content_change)
        elif is_content_change:
            _, audit_level = self.get_permission_level(PermissionName.ARTICLE_AUDIT, False)
            audit_permission = self.section_service.has_set_permission(
                permission=article.section.sectionpermission.article_audit,
                set_role=set_role,
                op=audit_level.is_gt_lv10())
            if not audit_permission and \
                (article.status == Article.ACTIVE or
                 article.status == Article.AUDIT or
                 article.status == Article.FAILED):
                article.status = status if Setting().ARTICLE_AUDIT else article.status
        article.save()
        return 200, ArticleService._article_to_dict(article=article)

    def _has_get_permission(self, article):
        section = article.section
        is_author = article.author_id == self.uid
        if is_author and article.status != Article.CANCEL:
            return True, True
        permission_level, _ = self.get_permission_level(PermissionName.ARTICLE_PERMISSION, False)
        if permission_level.is_gt_lv10():
            return True, True
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
            set_role = self.section_service.is_manager(section=section)
            if self.section_service.has_set_permission(
                    permission=section.sectionpermission.article_audit,
                    set_role=set_role):
                return True, True
            return article.privacy != Article.PRIVATE, False
        elif article.status == Article.CANCEL:
            cancel_level, _ = self.get_permission_level(PermissionName.ARTICLE_CANCEL, False)
            if cancel_level.is_gt_lv10():
                return True, True
            set_role = self.section_service.is_manager(section=section)
            if self.section_service.has_set_permission(
                    permission=section.sectionpermission.article_delete,
                    set_role=set_role):
                return True, True
        elif article.status == Article.AUDIT or article.status == Article.FAILED:
            audit_level, _ = self.get_permission_level(PermissionName.ARTICLE_AUDIT, False)
            if audit_level.is_gt_lv10():
                return True, True
            set_role = self.section_service.is_manager(section=section)
            if self.section_service.has_set_permission(
                    permission=section.sectionpermission.article_audit,
                    set_role=set_role):
                return True, True
        elif article.status == Article.DRAFT:
            set_role = self.section_service.is_manager(section=section)
            if self.section_service.has_set_permission(
                    permission=section.sectionpermission.article_draft,
                    set_role=set_role):
                return True, True
        elif article.status == Article.RECYCLED:
            set_role = self.section_service.is_manager(section=section)
            if self.section_service.has_set_permission(
                    permission=section.sectionpermission.article_recycled,
                    set_role=set_role):
                return True, True
        return False, False

    def _get_section(self, section_id):
        section = None
        if section_id:
            try:
                section = Section.objects.get(id=section_id)
                get_permission, read_permission = self.section_service.has_get_permission(section)
                if not get_permission:
                    raise ServiceError(code=400, message=ContentErrorMsg.SECTION_NOT_FOUND)
                if not read_permission:
                    raise ServiceError(code=403, message=ContentErrorMsg.SECTION_PERMISSION_DENIED)
                section_policy = section.sectionpolicy
                if section_policy.article_mute:
                    raise ServiceError(code=403, message=ContentErrorMsg.SECTION_PERMISSION_DENIED)
                if section_policy.max_articles is not None and \
                        Article.objects.filter(author_id=self.uid,
                                               section_id=section_id).count() >= section_policy.max_articles:
                    raise ServiceError(code=403, message=ContentErrorMsg.SECTION_PERMISSION_DENIED)
                start = now().date()
                end = start + timedelta(days=1)
                if section_policy.max_articles_one_day is not None and \
                        Article.objects.filter(author_id=self.uid,
                                               section_id=section_id,
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
            if section and Setting().ARTICLE_AUDIT:
                _, audit_level = self.get_permission_level(PermissionName.ARTICLE_AUDIT, False)
                set_role = self.section_service.is_manager(section=section)
                if self.section_service.has_set_permission(permission=section.sectionpermission.article_audit,
                                                           set_role=set_role,
                                                           op=audit_level.is_gt_lv10()):
                    return status
                raise ServiceError(code=403, message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
            elif status == Article.ACTIVE:
                return Article.ACTIVE
            raise ServiceError(code=403, message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
        if status == Article.CANCEL:
            if section and Setting().ARTICLE_CANCEL:
                _, cancel_level = self.get_permission_level(PermissionName.ARTICLE_CANCEL, False)
                set_role = self.section_service.is_manager(section=section)
                if self.section_service.has_set_permission(permission=section.sectionpermission.article_cancel,
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
            if section and Setting().ARTICLE_AUDIT:
                if is_content_change and status == Article.AUDIT:
                    return status
                _, audit_level = self.get_permission_level(PermissionName.ARTICLE_AUDIT, False)
                if self.section_service.has_set_permission(permission=section.sectionpermission.article_audit,
                                                           set_role=set_role,
                                                           op=audit_level.is_gt_lv10()):
                    return status
                if is_self and (status == Article.ACTIVE or
                                status == Article.FAILED):
                    return Article.AUDIT
                raise ServiceError(code=403, message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
            elif status == Article.ACTIVE:
                return status
        elif status == Article.CANCEL:
            if section and Setting().ARTICLE_CANCEL:
                _, cancel_level = self.get_permission_level(PermissionName.ARTICLE_CANCEL, False)
                if self.section_service.has_set_permission(permission=section.sectionpermission.article_cancel,
                                                           set_role=set_role,
                                                           op=cancel_level.is_gt_lv10()):
                    return status
        elif status == Article.DRAFT:
            if is_self or self.section_service.has_set_permission(
                    permission=section.sectionpermission.article_draft,
                    set_role=set_role):
                return status
        elif status == Article.RECYCLED:
            if is_self or self.section_service.has_set_permission(
                    permission=section.sectionpermission.article_recycled,
                    set_role=set_role):
                return status
        raise ServiceError(code=403, message=ContentErrorMsg.STATUS_PERMISSION_DENIED)

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
    def _article_to_dict(article, **kwargs):
        article_dict = model_to_dict(article)
        author_dict = model_to_dict(article.author)
        article_dict['author'] = {}
        for field in UserService.USER_PUBLIC_FIELD:
            article_dict['author'][field] = author_dict[field]
        last_editor_dict = model_to_dict(article.last_editor)
        article_dict['last_editor'] = {}
        for field in UserService.USER_PUBLIC_FIELD:
            article_dict['last_editor'][field] = last_editor_dict[field]
        for key in kwargs:
            article_dict[key] = kwargs[key]
        return article_dict

    @staticmethod
    def _status_or(a, b):
        return (a if isinstance(a, Q) else Q(status=int(a))) | Q(status=int(b))
