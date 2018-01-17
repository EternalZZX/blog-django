#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from django.db.models import Q

from blog.account.users.models import User
from blog.account.roles.models import Role, Permission, RolePermission
from blog.common.base import Service, Authorize, Grant
from blog.common.setting import PermissionName, PermissionLevel
from blog.common.error import ServiceError
from blog.common.message import ErrorMsg, AccountErrorMsg
from blog.common.utils import model_to_dict, paging


class RoleService(Service):
    ROLE_ALL_FIELD = ['id', 'name', 'nick', 'role_level', 'default', 'create_at']

    def get(self, role_id):
        self.has_permission(PermissionName.ROLE_SELECT)
        try:
            role = Role.objects.get(id=role_id)
            role_dict = RoleService._role_to_dict(role=role)
        except Role.DoesNotExist:
            raise ServiceError(code=404,
                               message=AccountErrorMsg.ROLE_NOT_FOUND)
        return 200, role_dict

    def list(self, page=0, page_size=10, order_field=None, order='desc',
             query=None, query_field=None):
        query_level, order_level = self.get_permission_level(PermissionName.ROLE_SELECT)
        roles = Role.objects.all()
        if order_field:
            if order_level >= PermissionLevel.LEVEL_1 and \
                            order_field in RoleService.ROLE_ALL_FIELD:
                if order == 'desc':
                    order_field = '-' + order_field
                roles = roles.order_by(order_field)
            else:
                raise ServiceError(code=403,
                                   message=ErrorMsg.ORDER_PERMISSION_DENIED)
        if query:
            if not query_field and query_level >= PermissionLevel.LEVEL_2:
                roles = roles.filter(Q(name__icontains=query) |
                                     Q(nick__icontains=query))
            elif query_level >= PermissionLevel.LEVEL_1:
                if query_field == 'name':
                    query_field = 'name__icontains'
                elif query_field == 'nick':
                    query_field = 'nick__icontains'
                elif query_level < PermissionLevel.LEVEL_9:
                    raise ServiceError(code=403,
                                       message=ErrorMsg.QUERY_PERMISSION_DENIED)
                query_dict = {query_field: query}
                roles = roles.filter(**query_dict)
        roles, total = paging(roles, page=page, page_size=page_size)
        role_dict_list = []
        for role in roles:
            role_dict_list.append(RoleService._role_to_dict(role=role))
        return 200, {'roles': role_dict_list, 'total': total}

    def create(self, name, nick=None, role_level=0, default=False, **kwargs):
        self.has_permission(PermissionName.ROLE_CREATE)
        RoleService._is_unique(model_obj=Role, name=name)
        nick = nick if nick else name
        role_level = int(role_level) if role_level else 0
        if default:
            Role.objects.filter(default=True).update(default=False)
        role = Role.objects.create(name=name,
                                   nick=nick,
                                   role_level=role_level,
                                   default=default)
        role_dict = model_to_dict(role)
        role_dict['permissions'] = RoleService._permission_create(role=role, **kwargs)
        return 201, role_dict

    def update(self, role_id, name=None, nick=None, role_level=None,
               default=None, **kwargs):
        self.has_permission(PermissionName.USER_UPDATE)
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            raise ServiceError(code=404,
                               message=AccountErrorMsg.ROLE_NOT_FOUND)
        if name and RoleService._is_unique(model_obj=Role, exclude_id=role_id, name=name):
            role.name = name
        if nick:
            role.nick = nick
        if role_level is not None:
            role.role_level = role_level
        if default is not None:
            if default:
                Role.objects.filter(default=True).update(default=False)
            role.default = default
        role.save()
        role = RoleService._permission_update(role=role, **kwargs)
        Grant().load_permission(role=role)
        return 200, RoleService._role_to_dict(role)

    def delete(self, delete_id):
        self.has_permission(PermissionName.ROLE_DELETE)
        result = {'id': delete_id}
        try:
            role = Role.objects.get(id=delete_id)
            result['name'], result['status'] = role.name, 'SUCCESS'
            users = User.objects.filter(role_id=delete_id)
            if users:
                default_roles = Role.objects.exclude(id=delete_id).filter(default=True)
                if default_roles:
                    users.update(role=default_roles[0])
                    for user in users:
                        Authorize().update_token(uuid=user.uuid, role_id=default_roles[0].id)
                else:
                    raise ServiceError(code=403, message=AccountErrorMsg.NO_DEFAULT_ROLE)
            role.delete()
        except Role.DoesNotExist:
            result['status'] = 'NOT_FOUND'
        return result

    @staticmethod
    def _role_permission_to_dict(role_permission):
        role_permission_dic = {
            'id': role_permission.id,
            'name': role_permission.permission.name,
            'nick': role_permission.permission.nick,
            'description': role_permission.permission.description,
            'status': role_permission.state
        }
        if role_permission.major_level is not None:
            role_permission_dic['major_level'] = role_permission.major_level
        if role_permission.minor_level is not None:
            role_permission_dic['minor_level'] = role_permission.minor_level
        if role_permission.value is not None:
            role_permission_dic['value'] = role_permission.value
        return role_permission_dic

    @staticmethod
    def _role_to_dict(role):
        role_dict = model_to_dict(role)
        del role_dict['permissions'][:]
        role_permissions = role.rolepermission_set.all()
        for role_permission in role_permissions:
            role_permission_dic = RoleService._role_permission_to_dict(role_permission)
            role_dict['permissions'].append(role_permission_dic)
        return role_dict

    @staticmethod
    def _json_loads(json_str):
        try:
            item = json.loads(json_str)
        except ValueError:
            raise ServiceError(message=AccountErrorMsg.PERMISSION_JSON_ERROR)
        state = item.get('state')
        major_level = item.get('major_level')
        minor_level = item.get('minor_level')
        value = item.get('value')
        state = state == 'true'
        major_level = int(major_level) if major_level else None
        minor_level = int(minor_level) if minor_level else None
        value = int(value) if value else None
        return state, major_level, minor_level, value

    @staticmethod
    def _permission_create(role, **kwargs):
        permissions = Permission.objects.all()
        permission_list = []
        for k, v in PermissionName():
            json_str = kwargs.get(v)
            if json_str:
                permission = permissions.get(name=v)
                state, major_level, minor_level, value = RoleService._json_loads(json_str=json_str)
                role_permission = RolePermission.objects.create(role=role,
                                                                permission=permission,
                                                                state=state,
                                                                major_level=major_level,
                                                                minor_level=minor_level,
                                                                value=value)
                role_permission_dict = RoleService._role_permission_to_dict(role_permission)
                permission_list.append(role_permission_dict)
        return permission_list

    @staticmethod
    def _permission_update(role, **kwargs):
        permissions = Permission.objects.all()
        for k, v in PermissionName():
            json_str = kwargs.get(v)
            if json_str:
                state, major_level, minor_level, value = RoleService._json_loads(json_str=json_str)
                try:
                    role_permission = role.rolepermission_set.get(permission__name=v)
                    role_permission.state = state
                    role_permission.major_level = major_level
                    role_permission.minor_level = minor_level
                    role_permission.value = value
                    role_permission.save()
                except RolePermission.DoesNotExist:
                    RolePermission.objects.create(role=role,
                                                  permission=permissions.get(name=v),
                                                  state=state,
                                                  major_level=major_level,
                                                  minor_level=minor_level,
                                                  value=value)
        return role
