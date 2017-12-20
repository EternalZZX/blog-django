#!/usr/bin/env python
# -*- coding: utf-8 -*-

from blog.account.roles.models import Role, Permission
from blog.common.base import Service


class RoleService(Service):
    def role_create(self, name, nick=None, role_level=0, default=False):
        role = Role.objects.create(name=name,
                                   nick=nick,
                                   role_level=role_level,
                                   default=default)
        permissions = Permission.objects.all()
        pass
