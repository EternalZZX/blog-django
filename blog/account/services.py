#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from Crypto.Hash import MD5

from django.db.models import Q

from blog.account.models import User, UserPrivacySetting, Role, Group
from blog.common.utils import paging, model_to_dict, encode
from blog.common.base import Service
from blog.common.error import ServiceError
from blog.common.message import AccountErrorMsg
from blog.common.setting import Setting, PermissionName, PermissionLevel


class UserService(Service):
    USER_PUBLIC_FIELD = ['nick', 'role', 'groups', 'remark', 'create_at']
    USER_ALL_FIELD = ['id', 'uuid', 'username', 'nick', 'role', 'groups', 'gender',
                      'email', 'phone', 'qq', 'address', 'remark', 'create_at']
    USER_PRIVACY_FIELD = ['gender_privacy', 'email_privacy', 'phone_privacy',
                          'qq_privacy', 'address_privacy']

    def user_get(self, user_uuid):
        query_level, _ = self.get_permission_level(PermissionName.USER_SELECT)
        try:
            if user_uuid != self.uuid and query_level < PermissionLevel.LEVEL_10:
                return_field = self.USER_PUBLIC_FIELD[:]
                user_privacy_setting = UserPrivacySetting.objects.get(user__uuid=user_uuid)
                for key in self.USER_PRIVACY_FIELD:
                    if getattr(user_privacy_setting, key) == UserPrivacySetting.PUBLIC:
                        return_field.append(key[:-8])
            else:
                return_field = self.USER_ALL_FIELD
            user = User.objects.values(*return_field).get(uuid=user_uuid)
        except (User.DoesNotExist, UserPrivacySetting.DoesNotExist):
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
        password_code = encode(password, user_uuid)
        nick = nick if nick else username
        user = User.objects.create(uuid=user_uuid, username=username, password=password_code,
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

    def user_update(self, user_uuid, username=None, old_password=None,
                    new_password=None, nick=None, role_id=None, group_ids=None,
                    gender=None, email=None, phone=None, qq=None, address=None,
                    remark=None, **kwargs):
        update_level, update_password_level = self.get_permission_level(PermissionName.USER_UPDATE)
        try:
            user = User.objects.get(uuid=user_uuid)
        except User.DoesNotExist:
            raise ServiceError(code=404,
                               message=AccountErrorMsg.USER_NOT_FOUND)
        if new_password and (self.uuid == user_uuid or
                             update_password_level >= PermissionLevel.LEVEL_9):
            if update_password_level < PermissionLevel.LEVEL_10:
                password_code = encode(old_password, user_uuid)
                if password_code != user.password:
                    raise ServiceError(code=403,
                                       message=AccountErrorMsg.PASSWORD_ERROR)
            user.password = encode(new_password, user_uuid)
        if self.uuid == user_uuid or update_level >= PermissionLevel.LEVEL_10:
            if nick and Setting.NICK_UPDATE:
                user.nick = nick
            if gender is not None:
                user.gender = gender if gender else None
            if email is not None:
                user.email = email if email else None
            if phone is not None:
                user.phone = phone if phone else None
            if qq is not None:
                user.qq = qq if qq else None
            if address is not None:
                user.address = address if address else None
            if remark is not None:
                user.remark = remark if remark else None
        if role_id and update_level >= PermissionLevel.LEVEL_10:
            user.role_id = role_id
        if update_level >= PermissionLevel.LEVEL_9:
            is_not_clear = True
            for group_id in group_ids:
                try:
                    group = Group.objects.get(id=group_id)
                    if is_not_clear:
                        user.groups.clear()
                        is_not_clear = False
                    user.groups.add(group)
                except Group.DoesNotExist:
                    pass
        user.save()
        user_dict = model_to_dict(user)
        del user_dict['password']
        return 200, user_dict
