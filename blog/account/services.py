#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from Crypto.Hash import MD5

from blog.account.models import User, Role, Group
from blog.common.utils import model_to_dict
from blog.common.base import Service
from blog.common.error import ServiceError
from blog.common.message import AccountErrorMsg
from blog.common.setting import PermissionName, PermissionLevel


class UserService(Service):
    def user_create(self, username, password, nick=None, role_id=None,
                    group_ids=None, gender=None, email=None, phone=None,
                    qq=None, address=None, remark=None):
        perm_level = self.get_permission_level(PermissionName.USER_CREATE)
        role = None
        if role_id:
            try:
                role = Role.objects.get(id=role_id)
                if perm_level < PermissionLevel.ADMIN_LEVEL and role.role_level >= self.role_level:
                    raise ServiceError(code=403,
                                       message=AccountErrorMsg.ROLE_PERMISSION_DENIED)
            except Role.DoesNotExist:
                pass
        if not role:
            default_roles = Role.objects.filter(default=True)
            role = default_roles[0] if default_roles else None
        if User.objects.filter(username=username):
            raise ServiceError(message=AccountErrorMsg.DUPLICATE_USERNAME)
        md5 = MD5.new()
        md5.update(password)
        md5 = md5.hexdigest()
        user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, username.encode('utf-8')))
        user = User.objects.create(uuid=user_uuid, username=username, password=md5,
                                   nick=nick, role=role, gender=gender, email=email,
                                   phone=phone, qq=qq, address=address, remark=remark)
        for group_id in group_ids:
            try:
                user.groups.add(Group.objects.get(id=group_id))
            except Group.DoesNotExist:
                pass
        return 200, model_to_dict(user)
