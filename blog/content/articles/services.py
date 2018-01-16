#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from django.db.models import Q

from blog.common.base import Service
from blog.common.setting import Setting, PermissionName, PermissionLevel


class ArticleService(Service):
    def create(self):
        create_level, _ = self.get_permission_level(PermissionName.ARTICLE_CREATE)
        pass
