#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid
import time

from django.db.models import Q
from django.utils.timezone import now, timedelta

from blog.account.users.models import User
from blog.account.users.services import UserService
from blog.content.sections.models import Section
from blog.content.sections.services import SectionService
from blog.content.articles.models import Article
from blog.common.base import Service
from blog.common.error import ServiceError
from blog.common.message import ErrorMsg, ContentErrorMsg
from blog.common.utils import paging, model_to_dict
from blog.common.setting import Setting, PermissionName


class ArticleService(Service):
    def __init__(self, request):
        super(ArticleService, self).__init__(request=request)
        self.section_service = SectionService(request=request)

    def get(self, article_uuid):
        self.has_permission(PermissionName.ARTICLE_SELECT)
        try:
            article = Article.objects.get(uuid=article_uuid)
            if not self._has_get_permission(article=article):
                raise Article.DoesNotExist
            article_dict = ArticleService._article_to_dict(article=article)
        except Article.DoesNotExist:
            raise ServiceError(code=404,
                               message=ContentErrorMsg.ARTICLE_NOT_FOUND)
        return 200, article_dict

    def create(self, title, keywords=None, content=None, section_id=None,
               status=Article.AUDIT, privacy=Article.PUBLIC, read_level=100):
        self.has_permission(PermissionName.ARTICLE_CREATE)
        article_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, (title + self.uuid + str(time.time())).encode('utf-8')))
        keyword_str = ''
        for keyword in keywords:
            keyword_str = keyword_str + keyword + ';'
        keyword_str = keyword_str[:-1] if keyword_str else keyword_str
        section = self._get_section(section_id=section_id)
        status = self._get_create_status(status=status, section=section)
        privacy = self._get_privacy(privacy=privacy)
        read_level = self._get_read_level(read_level=read_level)
        article = Article.objects.create(uuid=article_uuid,
                                         title=title,
                                         keywords=keyword_str,
                                         content=content,
                                         author_id=self.uid,
                                         section=section,
                                         status=status,
                                         privacy=privacy,
                                         read_level=read_level)
        return 201, ArticleService._article_to_dict(article=article)

    def _has_get_permission(self, article):
        section = article.section
        is_author = article.author_id == self.uid
        if is_author and article.status != Article.CANCEL:
            return True
        permission_level, _ = self.get_permission_level(PermissionName.ARTICLE_PERMISSION, False)
        if permission_level.is_gt_lv10():
            return True
        _, read_permission = self.section_service.has_get_permission(article.section)
        if not read_permission:
            return False
        if article.status == Article.ACTIVE:
            privacy_level, _ = self.get_permission_level(PermissionName.ARTICLE_PRIVACY, False)
            read_permission_level, _ = self.get_permission_level(PermissionName.ARTICLE_READ, False)
            read_level = self.get_permission_value(PermissionName.READ_LEVEL, False)
            if (article.privacy == Article.PUBLIC or privacy_level.is_gt_lv10()) and \
                    (read_level >= article.read_level or read_permission_level.is_gt_lv10()):
                return True
            if self.section_service.is_manager(section=section).is_manager:
                return True
            return False
        if article.status == Article.CANCEL:
            cancel_level, _ = self.get_permission_level(PermissionName.ARTICLE_CANCEL, False)
            if cancel_level.is_gt_lv10():
                return True
            set_role = self.section_service.is_manager(section=section)
            return self.section_service.has_set_permission(permission=section.sectionpermission.article_delete,
                                                           set_role=set_role)
        if article.status == Article.AUDIT or article.status == Article.FAILED:
            audit_level, _ = self.get_permission_level(PermissionName.ARTICLE_AUDIT, False)
            if audit_level.is_gt_lv10():
                return True
            set_role = self.section_service.is_manager(section=section)
            return self.section_service.has_set_permission(permission=section.sectionpermission.article_audit,
                                                           set_role=set_role)
        if article.status == Article.DRAFT:
            set_role = self.section_service.is_manager(section=section)
            return self.section_service.has_set_permission(permission=section.sectionpermission.article_draft,
                                                           set_role=set_role)
        if article.status == Article.RECYCLED:
            set_role = self.section_service.is_manager(section=section)
            return self.section_service.has_set_permission(permission=section.sectionpermission.article_recycled,
                                                           set_role=set_role)
        return False

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
            return status if Setting().ARTICLE_AUDIT else Article.ACTIVE
        if status == Article.ACTIVE or status == Article.FAILED:
            _, audit_level = self.get_permission_level(PermissionName.ARTICLE_AUDIT, False)
            if not Setting().ARTICLE_AUDIT:
                return Article.ACTIVE
            elif section:
                set_role = self.section_service.is_manager(section=section)
                if self.section_service.has_set_permission(permission=section.sectionpermission.article_audit,
                                                           set_role=set_role,
                                                           op=audit_level.is_gt_lv10()):
                    return status
            raise ServiceError(code=403,
                               message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
        if status == Article.CANCEL:
            if section and Setting().ARTICLE_CANCEL:
                _, cancel_level = self.get_permission_level(PermissionName.ARTICLE_CANCEL, False)
                set_role = self.section_service.is_manager(section=section)
                if self.section_service.has_set_permission(permission=section.sectionpermission.article_cancel,
                                                           set_role=set_role,
                                                           op=cancel_level.is_gt_lv10()):
                    return status
            raise ServiceError(code=403,
                               message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
        return status

    # def _get_update_status(self, status, article):
    #     status = ArticleService.choices_format(status, Article.STATUS_CHOICES, article.status)
    #     if status == article.status:
    #         return status
    #     section = article.section
    #     is_author = article.author_id == self.uid
    #     audit_level, cancel_level = self.get_permission_level(PermissionName.ARTICLE_STATUS, False)
    #
    #     if status == Article.CANCEL and Setting().ARTICLE_CANCEL:
    #         if is_author and cancel_level.is_gt_lv1() or cancel_level.is_gt_lv10():
    #             return status
    #         elif section:
    #             set_role = self.section_service.is_manager(section=section)
    #             if self.section_service.has_set_permission(permission=section.sectionpermission.article_cancel,
    #                                                        set_role=set_role):
    #                 return status
    #     if status == Article.ACTIVE or status == Article.AUDIT or status == Article.FAILED:
    #         if status == Article.AUDIT and is_author or audit_level.is_gt_lv10():
    #             return status if Setting().ARTICLE_AUDIT else Article.ACTIVE
    #         elif section:
    #             set_role = self.section_service.is_manager(section=section)
    #             if self.section_service.has_set_permission(permission=section.sectionpermission.article_audit,
    #                                                        set_role=set_role):
    #                 return status if Setting().ARTICLE_AUDIT else Article.ACTIVE
    #     if status == Article.DRAFT and (is_author or ):
    #
    #
    #     raise ServiceError(code=403,
    #                        message=ContentErrorMsg.STATUS_PERMISSION_DENIED)

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
        for key in kwargs:
            article_dict[key] = kwargs[key]
        return article_dict
