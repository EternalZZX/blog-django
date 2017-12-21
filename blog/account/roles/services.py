#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from blog.account.roles.models import Role, Permission, RolePermission
from blog.common.base import Service
from blog.common.setting import PermissionName
from blog.common.error import ServiceError
from blog.common.message import AccountErrorMsg
from blog.common.utils import model_to_dict


class RoleService(Service):
    def get(self):
        pass

    def list(self):
        pass

    def create(self, name, nick=None, role_level=0, default=False, **kwargs):
        self.has_permission(PermissionName.ROLE_CREATE)
        RoleService._is_unique(name=name)
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
            str = kwargs.get(v)
            if str:
                item = json.loads(str)
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
                role_dict['permissions'].append(role_permission_dic)
        return 201, role_dict

    def update(self):
        pass

    def delete(self):
        pass

    @staticmethod
    def _is_unique(**kwargs):
        try:
            if Role.objects.get(**kwargs):
                raise ServiceError(message=AccountErrorMsg.DUPLICATE_IDENTITY)
        except Role.MultipleObjectsReturned:
            raise ServiceError(code=500, message=AccountErrorMsg.DUPLICATE_IDENTITY)
        except Role.DoesNotExist:
            return kwargs.values()[0]