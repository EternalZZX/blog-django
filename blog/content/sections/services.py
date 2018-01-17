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
from blog.common.message import ContentErrorMsg
from blog.common.utils import paging, model_to_dict
from blog.common.setting import Setting, PermissionName, PermissionLevel


class SectionService(Service):
    def get(self, section_id):
        get_level, _ = self.get_permission_level(PermissionName.SECTION_SELECT)
        try:
            section = Section.objects.get(id=section_id)
            if section.status == Section.CANCEL and get_level < PermissionLevel.LEVEL_10:
                raise Section.DoesNotExist
            if section.status == Section.VISIBLE_ONLY and get_level < PermissionLevel.LEVEL_10:
                not_in_roles, not_in_groups = True, True
                if section.only_roles:
                    not_in_roles = len(section.roles.filter(id=self.role_id)) == 0
                if not_in_roles and section.only_groups:
                    section_groups = section.groups.values('id').all()
                    user_groups = User.objects.get(uuid=self.uuid).groups.values('id').all()
                    not_in_groups = len(set(section_groups) & set(user_groups)) == 0
                if (section.only_roles or section.only_groups) and \
                        not_in_roles and not_in_groups:
                    raise Section.DoesNotExist
            section_dict = model_to_dict(section)
            moderators = section.moderators.values(*UserService.USER_PUBLIC_FIELD).all()
            section_dict['moderators'] = [model_to_dict(moderator) for moderator in moderators]
            assistants = section.assistants.values(*UserService.USER_PUBLIC_FIELD).all()
            section_dict['assistants'] = [model_to_dict(assistant) for assistant in assistants]
        except Section.DoesNotExist:
            raise ServiceError(code=404,
                               message=ContentErrorMsg.SECTION_NOT_FOUND)
        return 200, section_dict

    def create(self, name, nick=None, description=None, moderator_uuids=None,
               assistant_uuids=None, status=Section.ACTIVE, level=0,
               only_roles=False, role_ids=None, only_groups=False,
               group_ids=None):
        self.has_permission(PermissionName.SECTION_CREATE)
        SectionService._is_unique(model_obj=Section, name=name)
        nick = nick if nick else name
        status = SectionService._choices_format(status, Section.STATUS_CHOICES, Section.ACTIVE)
        level = int(level) if level else 0
        section = Section.objects.create(name=name,
                                         nick=nick,
                                         description=description,
                                         status=status,
                                         level=level,
                                         only_roles=only_roles,
                                         only_groups=only_groups)
        section_dict = model_to_dict(section)
        for moderator_uuid in moderator_uuids:
            try:
                section.moderators.add(User.objects.get(uuid=moderator_uuid))
                section_dict['moderators'].append(moderator_uuid)
            except User.DoesNotExist:
                pass
        for assistant_uuid in assistant_uuids:
            try:
                if assistant_uuid not in moderator_uuids:
                    section.assistants.add(User.objects.get(uuid=assistant_uuid))
                    section_dict['assistants'].append(assistant_uuid)
            except User.DoesNotExist:
                pass
        for role_id in role_ids:
            try:
                section.roles.add(Role.objects.get(id=role_id))
                section_dict['roles'].append(int(role_id))
            except Role.DoesNotExist:
                pass
        for group_id in group_ids:
            try:
                section.groups.add(Group.objects.get(id=group_id))
                section_dict['groups'].append(int(group_id))
            except Group.DoesNotExist:
                pass
        return 201, section_dict
