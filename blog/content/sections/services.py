#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db.models import Q

from blog.account.groups.models import Group
from blog.account.users.models import User
from blog.account.users.services import UserService
from blog.account.roles.models import Role
from blog.content.albums.models import Album
from blog.content.photos.models import Photo
from blog.content.sections.models import Section, SectionPermission
from blog.common.base import Service
from blog.common.error import ServiceError
from blog.common.message import ErrorMsg, AccountErrorMsg, ContentErrorMsg
from blog.common.utils import paging, model_to_dict
from blog.common.setting import PermissionName, Setting


class SectionService(Service):
    SECTION_ALL_FIELD = ['id', 'name', 'nick', 'description', 'cover',
                         'read_level', 'status', 'owner', 'moderators',
                         'assistants', 'only_roles', 'roles', 'only_groups',
                         'groups', 'create_at']
    SECTION_POLICY_FIELD = ['auto_audit', 'article_mute', 'reply_mute',
                            'max_articles', 'max_articles_one_day']
    SECTION_PERMISSION_FIELD = ['set_permission', 'delete_permission', 'set_owner',
                                'set_name', 'set_nick', 'set_description', 'set_cover',
                                'set_moderator', 'set_assistant', 'set_status',
                                'set_cancel', 'cancel_visible', 'set_read_level',
                                'set_read_user', 'set_policy', 'article_audit',
                                'article_edit', 'article_draft', 'article_recycled',
                                'article_cancel', 'article_delete', 'comment_audit',
                                'comment_edit', 'comment_recycled', 'comment_cancel',
                                'comment_delete']

    class SectionRole:
        def __init__(self, is_owner, is_moderator, is_assistant):
            self.is_owner = is_owner
            self.is_moderator = is_moderator
            self.is_assistant = is_assistant
            self.is_controller = is_owner or is_moderator
            self.is_manager = is_assistant or is_moderator or is_owner

    def get(self, section_id):
        self.has_permission(PermissionName.SECTION_SELECT)
        try:
            section = Section.objects.get(id=section_id)
            get_permission, read_permission = self.has_get_permission(section=section)
            if not get_permission:
                raise Section.DoesNotExist
            section_dict = SectionService._section_to_dict(section=section,
                                                           read_permission=read_permission)
            permission_dict = model_to_dict(section.sectionpermission)
            del permission_dict['section']
            section_dict['permission'] = permission_dict
            policy_dict = model_to_dict(section.sectionpolicy)
            del policy_dict['section']
            section_dict['policy'] = policy_dict
        except Section.DoesNotExist:
            raise ServiceError(code=404,
                               message=ContentErrorMsg.SECTION_NOT_FOUND)
        return 200, section_dict

    def list(self, page=0, page_size=10, order_field=None, order='desc',
             query=None, query_field=None):
        query_level, order_level = self.get_permission_level(PermissionName.SECTION_SELECT)
        sections = Section.objects.all()
        if order_field:
            if (order_level.is_gt_lv1() and order_field in SectionService.SECTION_ALL_FIELD) \
                    or order_level.is_gt_lv10():
                if order == 'desc':
                    order_field = '-' + order_field
                sections = sections.order_by(order_field)
            else:
                raise ServiceError(code=400,
                                   message=ErrorMsg.ORDER_PARAMS_ERROR)
        if query:
            if query_field and query_level.is_gt_lv1():
                if query_field == 'name':
                    query_field = 'name__icontains'
                elif query_field == 'nick':
                    query_field = 'nick__icontains'
                elif query_field == 'description':
                    query_field = 'description__icontains'
                elif query_level.is_lt_lv10():
                    raise ServiceError(code=403,
                                       message=ErrorMsg.QUERY_PERMISSION_DENIED)
                query_dict = {query_field: query}
                sections = sections.filter(**query_dict)
            elif query_level.is_gt_lv2():
                sections = sections.filter(Q(name__icontains=query) |
                                           Q(nick__icontains=query) |
                                           Q(description__icontains=query))
            else:
                raise ServiceError(code=403,
                                   message=ErrorMsg.QUERY_PERMISSION_DENIED)
        section_read_list = {}
        for section in sections:
            get_permission, read_permission = self.has_get_permission(section=section)
            if not get_permission:
                sections = sections.exclude(id=section.id)
            else:
                section_read_list[section.id] = read_permission
        sections, total = paging(sections, page=page, page_size=page_size)
        section_dict_list = []
        for section in sections:
            section_dict_list.append(SectionService._section_to_dict(section=section,
                                                                     read_permission=section_read_list[section.id]))
        return 200, {'sections': section_dict_list, 'total': total}

    def create(self, name, nick=None, description=None, cover_uuid=None,
               owner_uuid=None, moderator_uuids=None, assistant_uuids=None,
               status=Section.NORMAL, read_level=0, only_roles=False,
               role_ids=None, only_groups=False, group_ids=None, **kwargs):
        self.has_permission(PermissionName.SECTION_CREATE)
        SectionService.is_unique(model_obj=Section, name=name)
        nick = nick if nick else name
        owner_id = self.uid
        if owner_uuid:
            try:
                owner_id = User.objects.get(uuid=owner_uuid).id
            except User.DoesNotExist:
                raise ServiceError(message=AccountErrorMsg.USER_NOT_FOUND)
        cover = self._get_cover_url(user_id=self.uid, cover_uuid=cover_uuid)
        status = SectionService.choices_format(status, Section.STATUS_CHOICES, Section.NORMAL)
        read_level = int(read_level) if read_level else 0
        section = Section.objects.create(name=name,
                                         nick=nick,
                                         description=description,
                                         cover=cover,
                                         owner_id=owner_id,
                                         status=status,
                                         read_level=read_level,
                                         only_roles=only_roles,
                                         only_groups=only_groups)
        for moderator_uuid in moderator_uuids:
            try:
                section.moderators.add(User.objects.get(uuid=moderator_uuid))
            except User.DoesNotExist:
                pass
        for assistant_uuid in assistant_uuids:
            try:
                # if assistant_uuid not in moderator_uuids:
                section.assistants.add(User.objects.get(uuid=assistant_uuid))
            except User.DoesNotExist:
                pass
        for role_id in role_ids:
            try:
                section.roles.add(Role.objects.get(id=role_id))
            except Role.DoesNotExist:
                pass
        for group_id in group_ids:
            try:
                section.groups.add(Group.objects.get(id=group_id))
            except Group.DoesNotExist:
                pass
        section_dict = SectionService._section_to_dict(section=section)
        permission_dict = model_to_dict(SectionService._section_permission_update(section, **kwargs))
        del permission_dict['section']
        section_dict['permission'] = permission_dict
        policy_dict = model_to_dict(SectionService._section_policy_update(section, **kwargs))
        del policy_dict['section']
        section_dict['policy'] = policy_dict
        return 201, section_dict

    def update(self, section_id, name=None, nick=None, description=None,
               cover_uuid=None, owner_uuid=None, moderator_uuids=None,
               assistant_uuids=None, status=None, read_level=None,
               only_roles=False, role_ids=None, only_groups=False,
               group_ids=None, **kwargs):
        update_level, policy_level = self.get_permission_level(PermissionName.SECTION_UPDATE)
        op = update_level.is_gt_lv9()
        try:
            section = Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            raise ServiceError(code=404,
                               message=ContentErrorMsg.SECTION_NOT_FOUND)
        set_role = self.is_manager(user_uuid=self.uuid, section=section)
        permission = section.sectionpermission
        if name and self.has_set_permission(permission.set_name, set_role, op) and \
                SectionService.is_unique(model_obj=Section, exclude_id=section_id, name=name):
            section.name = name
        if nick and self.has_set_permission(permission.set_nick, set_role, op):
            section.nick = nick
        if description is not None and self.has_set_permission(permission.set_description, set_role, op):
            section.update_char_field('description', description)
        if cover_uuid is not None and self.has_set_permission(permission.set_cover, set_role, op):
            section.cover = self._get_cover_url(user_id=self.uid, cover_uuid=cover_uuid)
        if owner_uuid and self.has_set_permission(permission.set_owner, set_role, op):
            try:
                section.owner_id = User.objects.get(uuid=owner_uuid).id
            except User.DoesNotExist:
                raise ServiceError(message=AccountErrorMsg.USER_NOT_FOUND)
        if moderator_uuids is not None and self.has_set_permission(permission.set_moderator, set_role, op):
            section.update_m2m_field(section.moderators, User, moderator_uuids, id_field='uuid')
        if assistant_uuids is not None and self.has_set_permission(permission.set_assistant, set_role, op):
            section.update_m2m_field(section.assistants, User, assistant_uuids, id_field='uuid')
        if status is not None:
            if status != Section.CANCEL and self.has_set_permission(permission.set_status, set_role, op):
                section.status = SectionService.choices_format(status, Section.STATUS_CHOICES, Section.NORMAL)
            elif status == Section.CANCEL and self.has_set_permission(permission.set_cancel, set_role, op):
                section.status = Section.CANCEL
        if read_level is not None and self.has_set_permission(permission.set_read_level, set_role, op):
            section.read_level = int(read_level)
        if self.has_set_permission(permission.set_read_user, set_role, op):
            if only_roles is not None:
                section.only_roles = only_roles
            section.update_m2m_field(section.roles, Role, role_ids)
            if only_groups is not None:
                section.only_groups = only_groups
            section.update_m2m_field(section.groups, Group, group_ids)
        section.save()
        section_dict = SectionService._section_to_dict(section=section)
        if self.has_set_permission(permission.set_permission, set_role, update_level.is_gt_lv10()):
            permission_dict = model_to_dict(SectionService._section_permission_update(section, **kwargs))
        else:
            permission_dict = model_to_dict(section.sectionpermission)
        del permission_dict['section']
        section_dict['permission'] = permission_dict
        if self.has_set_permission(permission.set_policy, set_role, policy_level.is_gt_lv10()):
            policy_dict = model_to_dict(SectionService._section_policy_update(section, **kwargs))
        else:
            policy_dict = model_to_dict(section.sectionpolicy)
        del policy_dict['section']
        section_dict['policy'] = policy_dict
        return 200, section_dict

    def delete(self, delete_id, force):
        delete_level, cancel_level = self.get_permission_level(PermissionName.SECTION_DELETE)
        result = {'id': delete_id}
        try:
            section = Section.objects.get(id=delete_id)
            result['name'], result['status'] = section.nick, 'SUCCESS'
            set_role = self.is_manager(user_uuid=self.uuid, section=section)
            permission = section.sectionpermission
            if force:
                if self.has_set_permission(permission.delete_permission, set_role, delete_level.is_gt_lv10()):
                    section.delete()
                else:
                    raise ServiceError()
            else:
                if self.has_set_permission(permission.set_cancel, set_role, cancel_level.is_gt_lv10()):
                    section.status = Section.CANCEL
                    section.save()
                else:
                    raise ServiceError()
        except Section.DoesNotExist:
            result['status'] = 'NOT_FOUND'
        except ServiceError:
            result['status'] = 'PERMISSION_DENIED'
        return result

    def has_get_permission(self, section):
        get_level, read_level = self.get_permission_level(PermissionName.SECTION_PERMISSION, False)
        set_role = self.is_manager(user_uuid=self.uuid, section=section)
        if section.status == Section.CANCEL:
            cancel_visible = section.sectionpermission.cancel_visible
            if SectionService.has_set_permission(permission=cancel_visible,
                                                 set_role=set_role):
                return True, True
            elif get_level.is_gt_lv10():
                return True, read_level.is_gt_lv10()
            else:
                return False, False
        if set_role.is_manager:
            return True, True
        elif get_level.is_gt_lv9():
            return True, read_level.is_gt_lv9()
        else:
            not_in_roles, not_in_groups = True, True
            if section.only_roles:
                not_in_roles = len(section.roles.filter(id=self.role_id)) == 0
            if not_in_roles and section.only_groups:
                section_groups = section.groups.values('id').all()
                user_groups = User.objects.get(uuid=self.uuid).groups.values('id').all()
                not_in_groups = len(set(section_groups) & set(user_groups)) == 0
            if (section.only_roles or section.only_groups) and \
                    not_in_roles and not_in_groups:
                return section.status != Section.HIDE, False
            else:
                read_value = self.get_permission_value(PermissionName.READ_LEVEL)
                if section.read_level > read_value:
                    return section.status != Section.HIDE, False
        return True, True

    @staticmethod
    def has_set_permission(permission, set_role, op=False):
        if op or permission == SectionPermission.OWNER and set_role.is_owner or \
                permission == SectionPermission.MODERATOR and set_role.is_moderator or \
                permission == SectionPermission.MANAGER and set_role.is_manager:
            return True
        return False

    @staticmethod
    def is_manager(user_uuid, section):
        # Todo save section manager to redis
        is_owner = section.owner.uuid == user_uuid
        is_moderator, is_assistant = True, True
        try:
            section.moderators.get(uuid=user_uuid)
        except User.DoesNotExist:
            is_moderator = False
        try:
            section.assistants.get(uuid=user_uuid)
        except User.DoesNotExist:
            is_assistant = False
        return SectionService.SectionRole(is_owner, is_moderator, is_assistant)

    @staticmethod
    def _get_cover_url(user_id, cover_uuid):
        if not cover_uuid:
            return None
        try:
            photo = Photo.objects.get(Q(uuid=cover_uuid,
                                        author__id=user_id,
                                        privacy=Photo.PUBLIC) |
                                      Q(uuid=cover_uuid,
                                        album__system=Album.SECTION_COVER_ALBUM,
                                        privacy=Photo.PUBLIC))
            if Setting().PHOTO_THUMBNAIL and photo.image_middle:
                return photo.image_middle.url
            else:
                return photo.image_large.url
        except Photo.DoesNotExist:
            return None

    @staticmethod
    def _section_permission_update(section, **kwargs):
        section_permission = section.sectionpermission
        for key in kwargs:
            if key in SectionService.SECTION_PERMISSION_FIELD and kwargs[key]:
                value = int(kwargs[key])
                if value not in dict(SectionPermission.PERMISSION_CHOICES):
                    value = SectionPermission.OWNER
                setattr(section_permission, key, value)
        section_permission.save()
        return section_permission

    @staticmethod
    def _section_policy_update(section, **kwargs):
        section_policy = section.sectionpolicy
        for key in kwargs:
            if key in SectionService.SECTION_POLICY_FIELD and kwargs[key] is not None:
                if kwargs[key] == 'true':
                    value = True
                elif kwargs[key] == 'false':
                    value = False
                elif kwargs[key] == '':
                    value = None
                else:
                    value = int(kwargs[key])
                setattr(section_policy, key, value)
        section_policy.save()
        return section_policy

    @staticmethod
    def _section_to_dict(section, **kwargs):
        section_dict = model_to_dict(section)
        moderators = section.moderators.values(*UserService.USER_PUBLIC_FIELD).all()
        section_dict['moderators'] = [model_to_dict(moderator) for moderator in moderators]
        assistants = section.assistants.values(*UserService.USER_PUBLIC_FIELD).all()
        section_dict['assistants'] = [model_to_dict(assistant) for assistant in assistants]
        UserService.user_to_dict(section.owner, section_dict, 'owner')
        for key in kwargs:
            section_dict[key] = kwargs[key]
        return section_dict
