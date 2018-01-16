#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.db.models import Q

from blog.account.groups.models import Group
from blog.account.users.models import User
from blog.account.roles.models import Role
from blog.content.sections.models import Section
from blog.common.base import Service
from blog.common.utils import paging, model_to_dict
from blog.common.setting import Setting, PermissionName, PermissionLevel


class SectionService(Service):
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
