#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db.models import Q

from blog.account.groups.models import Group
from blog.account.users.models import User
from blog.account.roles.models import Role
from blog.account.users.services import UserService
from blog.content.sections.models import Section
from blog.common.base import Service
from blog.common.error import ServiceError
from blog.common.message import ErrorMsg, ContentErrorMsg
from blog.common.utils import paging, model_to_dict
from blog.common.setting import PermissionName


class SectionService(Service):
    SECTION_ALL_FIELD = ['id', 'name', 'nick', 'description', 'read_level',
                         'status', 'moderators', 'assistants', 'only_roles',
                         'roles', 'only_groups', 'groups', 'creator',
                         'create_at']

    def get(self, section_id):
        get_level, _ = self.get_permission_level(PermissionName.SECTION_SELECT)
        try:
            section = Section.objects.get(id=section_id)
            get_permission, rw_permission = self._has_section_permission(section=section, get_level=get_level)
            if not get_permission:
                raise Section.DoesNotExist
            section_dict = SectionService._section_to_dict(section=section,
                                                           rw_permission=rw_permission)
        except Section.DoesNotExist:
            raise ServiceError(code=404,
                               message=ContentErrorMsg.SECTION_NOT_FOUND)
        return 200, section_dict

    def list(self, page=0, page_size=10, order_field=None, order='desc',
             query=None, query_field=None):
        query_level, order_level = self.get_permission_level(PermissionName.SECTION_SELECT)
        sections = Section.objects.all()
        if order_field:
            if order_level.is_gt_lv1() and order_field in SectionService.SECTION_ALL_FIELD:
                if order == 'desc':
                    order_field = '-' + order_field
                    sections = sections.order_by(order_field)
            else:
                raise ServiceError(code=400,
                                   message=ErrorMsg.ORDER_PARAMS_ERROR)
        if query:
            if not query_field and query_level.is_gt_lv2():
                sections = sections.filter(Q(name__icontains=query) |
                                           Q(nick__icontains=query) |
                                           Q(description__icontains=query))
            elif query_level.is_gt_lv1():
                if query_field == 'name':
                    query_field = 'name__icontains'
                elif query_field == 'nick':
                    query_field = 'nick__icontains'
                elif query_field == 'description':
                    query_field = 'description__icontains'
                elif query_level.is_lt_lv9():
                    raise ServiceError(code=403,
                                       message=ErrorMsg.QUERY_PERMISSION_DENIED)
                query_dict = {query_field: query}
                sections = sections.filter(**query_dict)
        section_rw_list = {}
        for section in sections:
            get_permission, rw_permission = self._has_section_permission(section=section, get_level=query_level)
            if not get_permission:
                sections = sections.exclude(id=section.id)
            else:
                section_rw_list[section.id] = rw_permission
        sections, total = paging(sections, page=page, page_size=page_size)
        section_dict_list = []
        for section in sections:
            section_dict_list.append(SectionService._section_to_dict(section=section,
                                                                     rw_permission=section_rw_list[section.id]))
        return 200, {'sections': section_dict_list, 'total': total}

    def create(self, name, nick=None, description=None, moderator_uuids=None,
               assistant_uuids=None, status=Section.NORMAL, read_level=0,
               only_roles=False, role_ids=None, only_groups=False,
               group_ids=None):
        self.has_permission(PermissionName.SECTION_CREATE)
        SectionService.is_unique(model_obj=Section, name=name)
        nick = nick if nick else name
        status = SectionService.choices_format(status, Section.STATUS_CHOICES, Section.NORMAL)
        read_level = int(read_level) if read_level else 0
        section = Section.objects.create(name=name,
                                         nick=nick,
                                         description=description,
                                         status=status,
                                         read_level=read_level,
                                         only_roles=only_roles,
                                         only_groups=only_groups,
                                         creator_id=self.uid)
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
        return 201, section_dict

    def update(self, section_id, name=None, nick=None, description=None,
               moderator_uuids=None, assistant_uuids=None, status=Section.NORMAL,
               read_level=0, only_roles=False, role_ids=None, only_groups=False,
               group_ids=None):
        update_level, appoint_level = self.get_permission_level(PermissionName.SECTION_UPDATE)
        try:
            section = Section.objects.get(id=section_id)
        except Section.DoesNotExist:
            raise ServiceError(code=404,
                               message=ContentErrorMsg.SECTION_NOT_FOUND)
        is_moderator, is_assistant = self._is_manager(section=section)
        if update_level.is_gt_lv10() or is_moderator and update_level.is_gt_lv1():
            if name and SectionService.is_unique(model_obj=Section, exclude_id=section_id, name=name):
                section.name = name
            if nick:
                section.nick = nick
        if update_level.is_gt_lv10() or \
                (is_moderator or is_assistant) and update_level.is_gt_lv1():
            section.update_char_field('description', description)
        if appoint_level.is_gt_lv10() or is_moderator and appoint_level.is_gt_lv2():
            section.update_m2m_field(section.moderators, User, moderator_uuids, id_field='uuid')
        if appoint_level.is_gt_lv10() or is_moderator and appoint_level.is_gt_lv1():
            section.update_m2m_field(section.assistants, User, assistant_uuids, id_field='uuid')
        if update_level.is_gt_lv10() or is_moderator and update_level.is_gt_lv2():
            if status is not None:
                section.status = SectionService.choices_format(status, Section.STATUS_CHOICES, Section.NORMAL)
            if read_level is not None:
                section.read_level = int(read_level)
            if only_roles is not None:
                section.only_roles = only_roles
            section.update_m2m_field(section.roles, Role, role_ids)
            if only_groups is not None:
                section.only_groups = only_groups
            section.update_m2m_field(section.groups, Group, group_ids)
        section.save()
        return 200, SectionService._section_to_dict(section)

    def delete(self, delete_id, force):
        delete_level, force_level = self.get_permission_level(PermissionName.SECTION_DELETE)
        result = {'id': delete_id}
        try:
            section = Section.objects.get(id=delete_id)
            result['name'], result['status'] = section.nick, 'SUCCESS'
            is_moderator, _ = self._is_manager(section=section)
            if not is_moderator and delete_level.is_lt_lv10():
                raise ServiceError()
            if force and force_level.is_gt_lv10():
                section.delete()
            else:
                section.status = Section.CANCEL
                section.save()
        except Section.DoesNotExist:
            result['status'] = 'NOT_FOUND'
        except ServiceError:
            result['status'] = 'PERMISSION_DENIED'
        return result

    def _has_section_permission(self, section, get_level):
        is_moderator, is_assistant = self._is_manager(section=section)
        if is_moderator or is_assistant or get_level.is_gt_lv10():
            return True, True
        elif section.status == Section.CANCEL:
            return False, False
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
                section_value = self.get_permission_value(PermissionName.SECTION_SELECT)
                if section.read_level > section_value:
                    return section.status != Section.HIDE, False
        return True, True

    def _is_manager(self, section):
        is_moderator, is_assistant = True, True
        try:
            section.moderators.get(uuid=self.uuid)
        except User.DoesNotExist:
            is_moderator = False
        try:
            section.assistants.get(uuid=self.uuid)
        except User.DoesNotExist:
            is_assistant = False
        return is_moderator, is_assistant

    @staticmethod
    def _section_to_dict(section, **kwargs):
        section_dict = model_to_dict(section)
        moderators = section.moderators.values(*UserService.USER_PUBLIC_FIELD).all()
        section_dict['moderators'] = [model_to_dict(moderator) for moderator in moderators]
        assistants = section.assistants.values(*UserService.USER_PUBLIC_FIELD).all()
        section_dict['assistants'] = [model_to_dict(assistant) for assistant in assistants]
        creator_dict = model_to_dict(section.creator)
        section_dict['creator'] = {}
        for field in UserService.USER_PUBLIC_FIELD:
            section_dict['creator'][field] = creator_dict[field]
        for key in kwargs:
            section_dict[key] = kwargs[key]
        return section_dict
