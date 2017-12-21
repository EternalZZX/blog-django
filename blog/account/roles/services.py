#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from django.db.models import Q

from blog.account.roles.models import Role, Permission, RolePermission
from blog.common.base import Service
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
        RoleService.is_unique(model_obj=Role, name=name)
        nick = nick if nick else name
        role_level = int(role_level) if role_level else 0
        if default:
            Role.objects.filter(default=True).update(default=False)
        role = Role.objects.create(name=name,
                                   nick=nick,
                                   role_level=role_level,
                                   default=default)
        permissions = Permission.objects.all()
        role_dict = model_to_dict(role)
        for k, v in PermissionName():
            json_str = kwargs.get(v)
            if json_str:
                item = json.loads(json_str)
                permission = permissions.get(name=v)
                state = item.get('state') == 'true'
                major_level = item.get('major_level')
                minor_level = item.get('minor_level')
                value = item.get('value')
                major_level = int(major_level) if major_level else None
                minor_level = int(minor_level) if minor_level else None
                value = int(value) if value else None
                role_permission = RolePermission.objects.create(role=role,
                                                                permission=permission,
                                                                state=state,
                                                                major_level=major_level,
                                                                minor_level=minor_level,
                                                                value=value)
                role_permission_dic = RoleService._role_permission_to_dict(role_permission)
                role_dict['permissions'].append(role_permission_dic)
        return 201, role_dict

    def update(self):
        pass

    def delete(self):
        pass

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