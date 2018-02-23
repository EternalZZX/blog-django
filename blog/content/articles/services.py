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
    def create(self, title, keywords=None, content=None, actor_uuids=None, section_id=None,
               status=Article.ACTIVE, privacy=Article.PUBLIC, read_level=100):
        self.has_permission(PermissionName.ARTICLE_CREATE)
        article_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, (title + self.uuid + str(time.time())).encode('utf-8')))
        keyword_str = ''
        for keyword in keywords:
            keyword_str = keyword_str + keyword + ';'
        keyword_str = keyword_str[:-1] if keyword_str else keyword_str
        section = self._get_section(section_id=section_id)
        status = self._get_status(status=status)
        privacy, read_level = self._get_privacy(privacy=privacy, read_level=read_level)
        article = Article.objects.create(uuid=article_uuid,
                                         title=title,
                                         keywords=keyword_str,
                                         content=content,
                                         author_id=self.uid,
                                         section=section,
                                         status=status,
                                         privacy=privacy,
                                         read_level=read_level,
                                         last_editor_id=self.uid)
        for actor_uuid in actor_uuids:
            try:
                article.actors.add(User.objects.get(uuid=actor_uuid))
            except User.DoesNotExist:
                pass
        return 201, ArticleService._article_to_dict(article=article)

    def _get_section(self, section_id):
        section = None
        if section_id:
            try:
                section = Section.objects.get(id=section_id)
                get_permission, read_permission = SectionService(request=self.request).has_get_permission(section)
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

    def _get_status(self, status=Article.ACTIVE, article=None):
        audit_level, cancel_level = self.get_permission_level(PermissionName.ARTICLE_STATUS, False)
        if article:
            default, is_self = article.status, article.author_id == self.uid
        else:
            default, is_self = Article.AUDIT if Setting().ARTICLE_AUDIT else Article.ACTIVE, True
        status = ArticleService.choices_format(status, Article.STATUS_CHOICES, default)
        if article and status == article.status:
            return status
        if status == Article.CANCEL and \
                (not Setting().ARTICLE_CANCEL or
                 is_self and cancel_level.is_lt_lv1() or
                 not is_self and cancel_level.is_lt_lv10()):
            raise ServiceError(code=403,
                               message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
        if status == Article.ACTIVE and Setting().ARTICLE_AUDIT and audit_level.is_lt_lv10():
            raise ServiceError(code=403,
                               message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
        if status == Article.FAILED:
            if not Setting().ARTICLE_AUDIT:
                status = Article.ACTIVE
            elif audit_level.is_lt_lv10():
                raise ServiceError(code=403,
                                   message=ContentErrorMsg.STATUS_PERMISSION_DENIED)
        if status == Article.AUDIT and not Setting().ARTICLE_AUDIT:
            status = Article.ACTIVE
        return status

    def _get_privacy(self, privacy=Article.PUBLIC, read_level=100):
        privacy_level, content_level = self.get_permission_level(PermissionName.ARTICLE_PRIVACY, False)
        privacy = ArticleService.choices_format(privacy, Article.PRIVACY_CHOICES, Article.PUBLIC)
        if privacy == Article.PROTECTED and privacy_level.is_lt_lv1() or \
                privacy == Article.PRIVATE and privacy_level.is_lt_lv2():
            privacy = Article.PUBLIC
        read_level = int(read_level) if read_level else 100
        if content_level.is_lt_lv1():
            read_level = 100
        else:
            self_read_level = self.get_permission_value(PermissionName.READ_LEVEL)
            if read_level > self_read_level and content_level.is_lt_lv10():
                read_level = self_read_level
        return privacy, read_level

    @staticmethod
    def _article_to_dict(article, **kwargs):
        article_dict = model_to_dict(article)
        actors = article.actors.values(*UserService.USER_PUBLIC_FIELD).all()
        article_dict['actors'] = [model_to_dict(actor) for actor in actors]
        author_dict = model_to_dict(article.author)
        article_dict['author'] = {}
        for field in UserService.USER_PUBLIC_FIELD:
            article_dict['author'][field] = author_dict[field]
        for key in kwargs:
            article_dict[key] = kwargs[key]
        return article_dict
