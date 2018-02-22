#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from django.db.models import Q

from blog.content.sections.models import Section
from blog.content.sections.services import SectionService
from blog.content.articles.models import Article
from blog.common.base import Service
from blog.common.error import ServiceError
from blog.common.message import ErrorMsg, ContentErrorMsg
from blog.common.setting import Setting, PermissionName


class ArticleService(Service):
    def create(self, title, keyword=None, content=None,
               content_url=None, actor_ids=None, section_id=None,
               status=Article.ACTIVE, privacy=Article.PUBLIC, read_level=100):
        create_level, content_level = self.get_permission_level(PermissionName.ARTICLE_CREATE)
        article_uuid = str(uuid.uuid4())
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
                if section_policy.max_articles and \
                        Article.objects.filter(author_id=self.uid).count() >= section_policy.max_articles:
                    raise ServiceError(code=403, message=ContentErrorMsg.SECTION_PERMISSION_DENIED)
            except Section.DoesNotExist:
                raise ServiceError(code=400,
                                   message=ContentErrorMsg.SECTION_NOT_FOUND)
        status = ArticleService.choices_format(status, Article.STATUS_CHOICES, Article.ACTIVE)
        if status == Article.CANCEL and (not Setting().ARTICLE_CANCEL or create_level.is_lt_lv10()):
            status = Article.ACTIVE
        if status == Article.ACTIVE and Setting().ARTICLE_AUDIT and create_level.is_lt_lv10():
            status = Article.AUDIT
        privacy = ArticleService.choices_format(privacy, Article.PRIVACY_CHOICES, Article.PUBLIC)
        if privacy == Article.PRIVATE and create_level.is_lt_lv1() or \
                privacy == Article.PROTECTED and create_level.is_lt_lv2():
            privacy = Article.PUBLIC
        read_level = int(read_level) if read_level else 100
        if create_level.is_lt_lv3():
            read_level = 100
        article = Article.objects.create(uuid=article_uuid,
                                         title=title,
                                         keyword=keyword,
                                         content=content,
                                         content_url=content_url,
                                         author_id=self.uid,
                                         section=section,
                                         status=status,
                                         privacy=privacy,
                                         read_level=read_level,
                                         last_editor_id=self.uid)
