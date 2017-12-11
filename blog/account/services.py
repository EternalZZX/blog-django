#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from Crypto.Hash import MD5

from django.db.models import Q

from blog.account.models import User, UserPrivacySetting, Role, Group
from blog.common.utils import paging, model_to_dict
from blog.common.base import Service
from blog.common.error import ServiceError
from blog.common.message import AccountErrorMsg
from blog.common.setting import PermissionName, PermissionLevel


class UserService(Service):
    USER_PUBLIC_FIELD = ['nick', 'role', 'groups', 'remark', 'create_at']
    USER_ALL_FIELD = ['id', 'uuid', 'username', 'nick', 'role', 'groups', 'gender',
                      'email', 'phone', 'qq', 'address', 'remark', 'create_at']
    USER_PRIVACY_FIELD = ['gender_privacy', 'email_privacy', 'phone_privacy',
                          'qq_privacy', 'address_privacy']

    def user_get(self, user_uuid):
        query_level, _ = self.get_permission_level(PermissionName.USER_SELECT)
        if user_uuid != self.uuid and query_level < PermissionLevel.LEVEL_10:
            return_field = self.USER_PUBLIC_FIELD
        else:
            return_field = self.USER_ALL_FIELD
        try:
            user = User.objects.values(*return_field).get(uuid=user_uuid)
        except User.DoesNotExist:
            raise ServiceError(code=404,
                               message=AccountErrorMsg.USER_NOT_FOUND)
        return 200, user

    def user_list(self, page=0, page_size=10, order_field=None, order='desc',
                  query=None, query_field=None):
        query_level, order_level = self.get_permission_level(PermissionName.USER_SELECT)
        return_field = self.USER_PUBLIC_FIELD if \
            query_level < PermissionLevel.LEVEL_10 else self.USER_ALL_FIELD
        users = User.objects.values(*return_field).all()
        if order_field:
            if (order_level >= PermissionLevel.LEVEL_1 and
                    order_field in self.USER_PUBLIC_FIELD) \
                    or order_level >= PermissionLevel.LEVEL_10:
                if order == 'desc':
                    order_field = '-' + order_field
                users = users.order_by(order_field)
            else:
                raise ServiceError(code=403,
                                   message=AccountErrorMsg.ORDER_PERMISSION_DENIED)
        if query:
            if not query_field and query_level >= PermissionLevel.LEVEL_2:
                users = users.filter(Q(nick__icontains=query) |
                                     Q(role__nick__icontains=query) |
                                     Q(groups__name__icontains=query) |
                                     Q(remark__icontains=query))
            elif query_level >= PermissionLevel.LEVEL_1:
                if query_field == 'nick':
                    query_field = 'nick__icontains'
                elif query_field == 'role':
                    query_field = 'role__nick__icontains'
                elif query_field == 'group':
                    query_field = 'groups__name__icontains'
                elif query_field == 'remark':
                    query_field = 'remark__icontains'
                elif query_level < PermissionLevel.LEVEL_10:
                    raise ServiceError(code=403,
                                       message=AccountErrorMsg.QUERY_PERMISSION_DENIED)
                query_dict = {query_field: query}
                users = users.filter(Q(**query_dict))
        users, total = paging(users, page=page, page_size=page_size)
        return 200, {'users': [model_to_dict(user) for user in users], 'total': total}

    def user_create(self, username, password, nick=None, role_id=None,
                    group_ids=None, gender=None, email=None, phone=None,
                    qq=None, address=None, remark=None, **kwargs):
        create_level, _ = self.get_permission_level(PermissionName.USER_CREATE)
        role = None
        if role_id:
            try:
                role = Role.objects.get(id=role_id)
                if create_level < PermissionLevel.LEVEL_10 and role.role_level >= self.role_level:
                    raise ServiceError(code=403,
                                       message=AccountErrorMsg.ROLE_PERMISSION_DENIED)
            except Role.DoesNotExist:
                pass
        if not role:
            default_roles = Role.objects.filter(default=True)
            role = default_roles[0] if default_roles else None
        if User.objects.filter(username=username):
            raise ServiceError(message=AccountErrorMsg.DUPLICATE_USERNAME)
        user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, username.encode('utf-8')))
        md5 = MD5.new()
        md5.update(user_uuid)
        md5.update(password + md5.hexdigest())
        md5 = md5.hexdigest()
        nick = nick if nick else username
        user = User.objects.create(uuid=user_uuid, username=username, password=md5,
                                   nick=nick, role=role, gender=gender, email=email,
                                   phone=phone, qq=qq, address=address, remark=remark)
        user_privacy_setting = None
        for key in kwargs:
            if key in self.USER_PRIVACY_FIELD and kwargs[key]:
                if not user_privacy_setting:
                    user_privacy_setting = UserPrivacySetting.objects.get(user=user)
                setattr(user_privacy_setting, key, kwargs[key])
        if user_privacy_setting:
            user_privacy_setting.save()
        user_dict = model_to_dict(user)
        del user_dict['password']
        for group_id in group_ids:
            try:
                user.groups.add(Group.objects.get(id=group_id))
                user_dict['groups'].append(int(group_id))
            except Group.DoesNotExist:
                pass
        return 201, user_dict
