#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from django.db.models import Q

from blog.account.users.models import User, UserPrivacySetting
from blog.account.roles.models import Role
from blog.account.groups.models import Group
from blog.common.utils import paging, model_to_dict, encode
from blog.common.base import Authorize, Service
from blog.common.error import ServiceError
from blog.common.message import ErrorMsg, AccountErrorMsg
from blog.common.setting import Setting, PermissionName, PermissionLevel


class UserService(Service):
    USER_PUBLIC_FIELD = ['nick', 'role', 'groups', 'remark', 'create_at']
    USER_ALL_FIELD = ['id', 'uuid', 'username', 'nick', 'role', 'groups',
                      'gender', 'email', 'phone', 'qq', 'address', 'remark',
                      'create_at']
    USER_MANAGE_FIELD = ['status']
    USER_PRIVACY_FIELD = ['gender_privacy', 'email_privacy', 'phone_privacy',
                          'qq_privacy', 'address_privacy']

    def get(self, user_uuid):
        query_level, _ = self.get_permission_level(PermissionName.USER_SELECT)
        try:
            user_dict = {}
            user_privacy_setting = UserPrivacySetting.objects.get(user__uuid=user_uuid)
            if user_uuid != self.uuid and query_level < PermissionLevel.LEVEL_9:
                return_field = UserService.USER_PUBLIC_FIELD[:]
                for key in UserService.USER_PRIVACY_FIELD:
                    if getattr(user_privacy_setting, key) == UserPrivacySetting.PUBLIC:
                        return_field.append(key[:-8])
            else:
                return_field = UserService.USER_ALL_FIELD[:]
                user_dict = model_to_dict(user_privacy_setting)
                if query_level >= PermissionLevel.LEVEL_10:
                    for key in UserService.USER_MANAGE_FIELD:
                        return_field.append(key)
            query_dict = {'uuid': user_uuid}
            if query_level < PermissionLevel.LEVEL_10:
                query_dict['status'] = User.ACTIVE
            user = User.objects.values(*return_field).get(**query_dict)
            user_dict.update(user)
        except (User.DoesNotExist, UserPrivacySetting.DoesNotExist):
            raise ServiceError(code=404,
                               message=AccountErrorMsg.USER_NOT_FOUND)
        return 200, user_dict

    def list(self, page=0, page_size=10, order_field=None, order='desc',
             query=None, query_field=None):
        query_level, order_level = self.get_permission_level(PermissionName.USER_SELECT)
        if query_level < PermissionLevel.LEVEL_9:
            return_field = UserService.USER_PUBLIC_FIELD
        elif query_level >= PermissionLevel.LEVEL_10:
            return_field = UserService.USER_ALL_FIELD[:]
            for key in UserService.USER_MANAGE_FIELD:
                return_field.append(key)
        else:
            return_field = UserService.USER_ALL_FIELD
        users = User.objects.values(*return_field).all()
        if query_level < PermissionLevel.LEVEL_10:
            users = users.filter(status=User.ACTIVE)
        if order_field:
            if (order_level >= PermissionLevel.LEVEL_1 and
                    order_field in UserService.USER_PUBLIC_FIELD) \
                    or order_level >= PermissionLevel.LEVEL_10:
                if order == 'desc':
                    order_field = '-' + order_field
                users = users.order_by(order_field)
            else:
                raise ServiceError(code=403,
                                   message=ErrorMsg.ORDER_PERMISSION_DENIED)
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
                elif query_level < PermissionLevel.LEVEL_9:
                    raise ServiceError(code=403,
                                       message=ErrorMsg.QUERY_PERMISSION_DENIED)
                query_dict = {query_field: query}
                users = users.filter(**query_dict)
        users, total = paging(users, page=page, page_size=page_size)
        return 200, {'users': [model_to_dict(user) for user in users], 'total': total}

    def create(self, username, password, nick=None, role_id=None,
               group_ids=None, gender=None, email=None, phone=None,
               qq=None, address=None, status=User.ACTIVE, remark=None,
               **kwargs):
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
        UserService.is_unique(model_obj=User, username=username)
        user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, username.encode('utf-8')))
        password_code = encode(password, user_uuid)
        nick = nick if nick else username
        gender = UserService._choices_format(gender, User.GENDER_CHOICES)
        if Setting.USER_CANCEL:
            status = UserService._choices_format(status, User.STATUS_CHOICES, User.ACTIVE)
        else:
            status = User.ACTIVE
        email = None if email in (None, '') else UserService.is_unique(model_obj=User, email=email)
        phone = None if phone in (None, '') else UserService.is_unique(model_obj=User, phone=phone)
        user = User.objects.create(uuid=user_uuid, username=username, password=password_code,
                                   nick=nick, role=role, gender=gender, email=email,
                                   phone=phone, qq=qq, address=address, status=status,
                                   remark=remark)
        user_dict = model_to_dict(UserService._user_privacy_update(user, **kwargs))
        user_dict.update(model_to_dict(user))
        del user_dict['password']
        for group_id in group_ids:
            try:
                user.groups.add(Group.objects.get(id=group_id))
                user_dict['groups'].append(int(group_id))
            except Group.DoesNotExist:
                pass
        return 201, user_dict

    def update(self, user_uuid, username=None, old_password=None,
               new_password=None, nick=None, role_id=None, group_ids=None,
               gender=None, email=None, phone=None, qq=None, address=None,
               status=None, remark=None, **kwargs):
        update_level, update_password_level = self.get_permission_level(PermissionName.USER_UPDATE)
        if self.uuid != user_uuid and update_level < PermissionLevel.LEVEL_10:
            raise ServiceError(code=403,
                               message=AccountErrorMsg.UPDATE_PERMISSION_DENIED)
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
        if username and Setting.USERNAME_UPDATE and UserService.is_unique(model_obj=User, username=username):
            user.username = username
        if nick and Setting.NICK_UPDATE:
            user.nick = nick
        if gender is not None:
            user.gender = UserService._choices_format(gender, User.GENDER_CHOICES)
        if status is not None:
            user.status = UserService._choices_format(status, User.STATUS_CHOICES, User.ACTIVE)
            if user.status == User.CANCEL:
                Authorize().cancel_token(uuid=user_uuid)
        if email is not None:
            if email == '':
                user.email = None
            elif UserService.is_unique(model_obj=User, email=email):
                user.email = email
        if phone is not None:
            if phone == '':
                user.phone = None
            elif UserService.is_unique(model_obj=User, phone=phone):
                user.phone = phone
        user.update_char_field('qq', qq)
        user.update_char_field('address', address)
        user.update_char_field('remark', remark)
        if role_id and update_level >= PermissionLevel.LEVEL_10:
            try:
                user.role = Role.objects.get(id=role_id)
                Authorize().update_token(uuid=user_uuid, role_id=role_id)
            except Role.DoesNotExist:
                raise ServiceError(code=404, message=AccountErrorMsg.ROLE_NOT_FOUND)
        if group_ids is not None and update_level >= PermissionLevel.LEVEL_10:
            user.groups.clear()
            for group_id in group_ids:
                try:
                    user.groups.add(Group.objects.get(id=group_id))
                except Group.DoesNotExist:
                    pass
        user.save()
        user_dict = model_to_dict(UserService._user_privacy_update(user, **kwargs))
        user_dict.update(model_to_dict(user))
        del user_dict['password']
        return 200, user_dict

    def delete(self, delete_id, force):
        delete_level, force_level = self.get_permission_level(PermissionName.USER_DELETE)
        result = {'id': delete_id}
        try:
            user = User.objects.get(uuid=delete_id)
            result['name'], result['status'] = user.username, 'SUCCESS'
            if delete_id != self.uuid and delete_level < PermissionLevel.LEVEL_10 \
                    and user.role.role_level >= self.role_level:
                raise ServiceError()
            if not Setting.USER_CANCEL or \
                    (force and force_level >= PermissionLevel.LEVEL_10):
                user.delete()
            else:
                user.status = User.CANCEL
                user.save()
                Authorize().cancel_token(uuid=delete_id)
        except User.DoesNotExist:
            result['status'] = 'NOT_FOUND'
        except ServiceError:
            result['status'] = 'PERMISSION_DENIED'
        return result

    @staticmethod
    def _choices_format(value, choices, default=None):
        if value in (None, ''):
            return default
        value = int(value)
        return value if value in dict(choices) else default

    @staticmethod
    def _user_privacy_update(user, **kwargs):
        user_privacy_setting = UserPrivacySetting.objects.get(user=user)
        for key in kwargs:
            if key in UserService.USER_PRIVACY_FIELD and kwargs[key]:
                value = int(kwargs[key])
                if value not in dict(UserPrivacySetting.PRIVACY_CHOICES):
                    value = UserPrivacySetting.PRIVATE
                setattr(user_privacy_setting, key, value)
        user_privacy_setting.save()
        return user_privacy_setting
