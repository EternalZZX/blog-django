#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from django.db.models import Q

from blog.account.users.models import User, UserPrivacySetting
from blog.account.roles.models import Role
from blog.account.groups.models import Group
from blog.content.albums.models import Album
from blog.content.photos.models import Photo
from blog.common.utils import paging, model_to_dict, encode
from blog.common.base import Authorize, Service
from blog.common.error import ServiceError
from blog.common.message import ErrorMsg, AccountErrorMsg
from blog.common.setting import Setting, PermissionName


class UserService(Service):
    USER_PUBLIC_FIELD = ['uuid', 'nick', 'avatar', 'role', 'groups',
                         'remark', 'create_at']
    USER_ALL_FIELD = ['id', 'uuid', 'username', 'nick', 'avatar', 'role',
                      'groups', 'gender', 'email', 'phone', 'qq', 'address',
                      'remark', 'create_at']
    USER_MANAGE_FIELD = ['status']
    USER_PRIVACY_FIELD = ['gender_privacy', 'email_privacy', 'phone_privacy',
                          'qq_privacy', 'address_privacy']

    def get(self, user_uuid):
        self.has_permission(PermissionName.USER_SELECT)
        privacy_level, _ = self.get_permission_level(PermissionName.USER_PRIVACY, False)
        _, cancel_level = self.get_permission_level(PermissionName.USER_CANCEL, False)
        try:
            privacy_dict = {}
            user_privacy_setting = UserPrivacySetting.objects.get(user__uuid=user_uuid)
            if user_uuid != self.uuid and privacy_level.is_lt_lv9():
                return_field = UserService.USER_PUBLIC_FIELD[:]
                for key in UserService.USER_PRIVACY_FIELD:
                    if getattr(user_privacy_setting, key) == UserPrivacySetting.PUBLIC:
                        return_field.append(key[:-8])
            else:
                return_field = UserService.USER_ALL_FIELD[:]
                privacy_dict = model_to_dict(user_privacy_setting)
                del privacy_dict['user']
                if privacy_level.is_gt_lv10():
                    for key in UserService.USER_MANAGE_FIELD:
                        return_field.append(key)
            query_dict = {'uuid': user_uuid}
            if cancel_level.is_lt_lv10():
                query_dict['status'] = User.ACTIVE
            user_dict = User.objects.values(*return_field).get(**query_dict)
            if privacy_dict:
                user_dict['privacy_setting'] = privacy_dict
        except (User.DoesNotExist, UserPrivacySetting.DoesNotExist):
            raise ServiceError(code=404,
                               message=AccountErrorMsg.USER_NOT_FOUND)
        return 200, user_dict

    def list(self, page=0, page_size=10, order_field=None, order='desc',
             query=None, query_field=None):
        query_level, order_level = self.get_permission_level(PermissionName.USER_SELECT)
        privacy_level, _ = self.get_permission_level(PermissionName.USER_PRIVACY, False)
        _, cancel_level = self.get_permission_level(PermissionName.USER_CANCEL, False)
        if privacy_level.is_lt_lv9():
            return_field = UserService.USER_PUBLIC_FIELD
        else:
            return_field = UserService.USER_ALL_FIELD[:]
            if privacy_level.is_gt_lv10():
                for key in UserService.USER_MANAGE_FIELD:
                    return_field.append(key)
        users = User.objects.values(*return_field).all()
        if cancel_level.is_lt_lv10():
            users = users.filter(status=User.ACTIVE)
        if order_field:
            if (order_level.is_gt_lv1() and order_field in return_field) \
                    or order_level.is_gt_lv10():
                if order == 'desc':
                    order_field = '-' + order_field
                users = users.order_by(order_field)
            else:
                raise ServiceError(code=403,
                                   message=ErrorMsg.ORDER_PERMISSION_DENIED)
        if query:
            if query_field and query_level.is_gt_lv1():
                if query_field == 'nick':
                    query_field = 'nick__icontains'
                elif query_field == 'role':
                    query_field = 'role__nick__icontains'
                elif query_field == 'group':
                    query_field = 'groups__name__icontains'
                elif query_field == 'remark':
                    query_field = 'remark__icontains'
                elif query_level.is_lt_lv10():
                    raise ServiceError(code=403,
                                       message=ErrorMsg.QUERY_PERMISSION_DENIED)
                query_dict = {query_field: query}
                users = users.filter(**query_dict)
            elif query_level.is_gt_lv2():
                users = users.filter(Q(nick__icontains=query) |
                                     Q(role__nick__icontains=query) |
                                     Q(groups__name__icontains=query) |
                                     Q(remark__icontains=query))
            else:
                raise ServiceError(code=403,
                                   message=ErrorMsg.QUERY_PERMISSION_DENIED)
        users, total = paging(users, page=page, page_size=page_size)
        return 200, {'users': [model_to_dict(user) for user in users], 'total': total}

    def create(self, username, password, nick=None, role_id=None,
               group_ids=None, gender=None, email=None, phone=None,
               qq=None, address=None, status=User.ACTIVE, remark=None,
               **kwargs):
        self.has_permission(PermissionName.USER_CREATE)
        role = None
        if role_id:
            role = self._get_role(role_id=role_id)
        if not role:
            default_roles = Role.objects.filter(default=True)
            if not default_roles:
                raise ServiceError(message=AccountErrorMsg.NO_DEFAULT_ROLE)
            role = default_roles[0] if default_roles else None
        UserService.is_unique(model_obj=User, username=username)
        user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, username.encode('utf-8')))
        password_code = encode(password, user_uuid)
        nick = nick if nick else username
        gender = UserService.choices_format(gender, User.GENDER_CHOICES)
        status = self._get_status(status=status)
        email = None if email in (None, '') else UserService.is_unique(model_obj=User, email=email)
        phone = None if phone in (None, '') else UserService.is_unique(model_obj=User, phone=phone)
        user = User.objects.create(uuid=user_uuid, username=username, password=password_code,
                                   nick=nick, role=role, gender=gender, email=email,
                                   phone=phone, qq=qq, address=address, status=status,
                                   remark=remark)
        user_dict = model_to_dict(user)
        del user_dict['password']
        privacy_dict = model_to_dict(UserService._user_privacy_update(user, **kwargs))
        del privacy_dict['user']
        user_dict['privacy_setting'] = privacy_dict
        for group_id in group_ids:
            try:
                user.groups.add(Group.objects.get(id=group_id))
                user_dict['groups'].append(int(group_id))
            except Group.DoesNotExist:
                pass
        return 201, user_dict

    def update(self, user_uuid, username=None, old_password=None,
               new_password=None, nick=None, avatar_uuid=None, role_id=None,
               group_ids=None, gender=None, email=None, phone=None, qq=None,
               address=None, status=None, remark=None, **kwargs):
        update_level, update_password_level = self.get_permission_level(PermissionName.USER_UPDATE)
        is_self = self.uuid == user_uuid
        if not is_self and update_level.is_lt_lv9():
            raise ServiceError(code=403, message=AccountErrorMsg.UPDATE_PERMISSION_DENIED)
        try:
            user = User.objects.get(uuid=user_uuid)
            if not is_self and update_level.is_lt_lv10() and \
                    user.role.role_level >= self.role_level:
                raise ServiceError(code=403, message=AccountErrorMsg.UPDATE_PERMISSION_DENIED)
        except User.DoesNotExist:
            raise ServiceError(code=404, message=AccountErrorMsg.USER_NOT_FOUND)
        if new_password and (is_self or update_password_level.is_gt_lv9()):
            if update_password_level.is_lt_lv10():
                password_code = encode(old_password, user_uuid)
                if password_code != user.password:
                    raise ServiceError(code=403, message=AccountErrorMsg.PASSWORD_ERROR)
            user.password = encode(new_password, user_uuid)
        if username and Setting().USERNAME_UPDATE and UserService.is_unique(model_obj=User,
                                                                            exclude_id=user.id,
                                                                            username=username):
            user.username = username
        if nick and Setting().NICK_UPDATE:
            user.nick = nick
        if avatar_uuid is not None:
            user.avatar = self._get_avatar_url(user_uuid=user.uuid, avatar_uuid=avatar_uuid)
        if gender is not None:
            user.gender = UserService.choices_format(gender, User.GENDER_CHOICES)
        if status is not None:
            user.status = self._get_status(status=status)
            if user.status == User.CANCEL:
                Authorize().cancel_token(uuid=user_uuid)
        if email is not None:
            if email == '':
                user.email = None
            elif UserService.is_unique(model_obj=User, exclude_id=user.id, email=email):
                user.email = email
        if phone is not None:
            if phone == '':
                user.phone = None
            elif UserService.is_unique(model_obj=User, exclude_id=user.id, phone=phone):
                user.phone = phone
        user.update_char_field('qq', qq)
        user.update_char_field('address', address)
        user.update_char_field('remark', remark)
        if role_id:
            user.role = self._get_update_role(role_id=role_id, user=user)
            Authorize().update_token(uuid=user_uuid, role_id=role_id)
        if group_ids is not None and update_level.is_gt_lv10():
            user.groups.clear()
            for group_id in group_ids:
                try:
                    user.groups.add(Group.objects.get(id=group_id))
                except Group.DoesNotExist:
                    pass
        user.save()
        user_dict = model_to_dict(user)
        del user_dict['password']
        privacy_dict = model_to_dict(UserService._user_privacy_update(user, **kwargs))
        del privacy_dict['user']
        user_dict['privacy_setting'] = privacy_dict
        return 200, user_dict

    def delete(self, delete_id, force):
        if force:
            self.has_permission(PermissionName.USER_DELETE)
        else:
            self.has_permission(PermissionName.USER_CANCEL)
        result = {'id': delete_id}
        try:
            user = User.objects.get(uuid=delete_id)
            result['name'], result['status'] = user.username, 'SUCCESS'
            if force:
                if self._has_delete_permission(delete_id=delete_id, user=user):
                    user.delete()
                else:
                    raise ServiceError()
            else:
                if Setting().USER_CANCEL and self._has_cancel_permission(delete_id=delete_id, user=user):
                    user.status = User.CANCEL
                    user.save()
                else:
                    raise ServiceError()
            Authorize().cancel_token(uuid=delete_id)
        except User.DoesNotExist:
            result['status'] = 'NOT_FOUND'
        except ServiceError:
            result['status'] = 'PERMISSION_DENIED'
        return result

    def _get_status(self, status):
        status_level, _ = self.get_permission_level(PermissionName.USER_STATUS, False)
        if status_level.is_gt_lv10():
            status = UserService.choices_format(status, User.STATUS_CHOICES, User.ACTIVE)
            if status == User.CANCEL and not Setting().USER_CANCEL:
                status = User.ACTIVE
        else:
            status = User.ACTIVE
        return status

    def _get_update_role(self, role_id, user):
        user_role_level, set_role_level = self.get_permission_level(PermissionName.USER_ROLE, False)
        if user_role_level.is_gt_lv10() or \
                user_role_level.is_gt_lv9() and user.role.role_level >= self.role_level:
            return self._get_role(role_id=role_id, set_role_level=set_role_level)
        else:
            raise ServiceError(code=403, message=AccountErrorMsg.UPDATE_PERMISSION_DENIED)

    def _get_role(self, role_id, set_role_level=None):
        if not set_role_level:
            _, set_role_level = self.get_permission_level(PermissionName.USER_ROLE, False)
        try:
            role = Role.objects.get(id=role_id)
            if set_role_level.is_gt_lv10() or role.default or \
                    set_role_level.is_gt_lv9() and role.role_level < self.role_level:
                return role
            else:
                raise ServiceError(code=403,
                                   message=AccountErrorMsg.ROLE_PERMISSION_DENIED)
        except Role.DoesNotExist:
            raise ServiceError(message=AccountErrorMsg.ROLE_NOT_FOUND)

    def _has_delete_permission(self, delete_id, user):
        delete_level, _ = self.get_permission_level(PermissionName.USER_DELETE, False)
        is_self = delete_id == self.uuid
        if delete_level.is_gt_lv10() or is_self and delete_level.is_gt_lv1() or \
                delete_level.is_gt_lv9() and self.role_level > user.role.role_level:
            return True
        return False

    def _has_cancel_permission(self, delete_id, user):
        cancel_level, _ = self.get_permission_level(PermissionName.USER_CANCEL, False)
        is_self = delete_id == self.uuid
        if cancel_level.is_gt_lv10() or is_self and cancel_level.is_gt_lv1() or \
                cancel_level.is_gt_lv9() and self.role_level > user.role.role_level:
            return True
        return False

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

    @staticmethod
    def _get_avatar_url(user_uuid, avatar_uuid):
        try:
            photo = Photo.objects.get(Q(uuid=avatar_uuid, author__uuid=user_uuid) |
                                      Q(uuid=avatar_uuid, album__system=Album.AVATAR_ALBUM))
            if Setting().PHOTO_THUMBNAIL and photo.image_small:
                return photo.image_small.url
            else:
                return photo.image_large.url
        except Photo.DoesNotExist:
            return None
