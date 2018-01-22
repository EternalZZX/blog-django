#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@apiDefine SECTION_SELECT
版块查询权限
1. MAJOR LEVEL10
- Section Get 可获取注销隐藏版块
- Section List 可获取注销隐藏版块
2. MAJOR LEVEL9
- Section List 可精确搜索所有字段
3. MAJOR LEVEL2
- Section List 可模糊搜索名称字段
4. MAJOR LEVEL1
- Section List 可精确搜索名称字段
5. MINOR LEVEL1
- Section List 可排序字段
6. VALUE
- Section Get 可获取大于等于其Level的版块
- Section List 可获取大于等于其Level的版块
7. moderators & assistants
- Section Get 可获取注销隐藏版块
- Section List 可获取注销隐藏版块
"""

"""
@apiDefine SECTION_CREATE
版块创建权限
- 版块创建权限
"""

"""
@apiDefine SECTION_UPDATE
版块编辑权限
1. MAJOR LEVEL10
- Section Update 可编辑所有版块
2. MAJOR LEVEL2
- Section Update 身为版主时可编辑版块名称、昵称、描述、状态、权限字段
3. MAJOR LEVEL1
- Section Update 身为版主时可编辑版块名称、昵称、描述
- Section Update 身为副版主时可编辑版块描述
4. MINOR LEVEL10
- Section Update 可任命所有版块版主、副版主
5. MINOR LEVEL2
- Section Update 身为版主时可任命版主、副版主
6. MINOR LEVEL1
- Section Update 身为版主时可任命副版主
"""

"""
@apiDefine SECTION_DELETE
版块删除权限
1. MAJOR LEVEL10
- Section Delete 可删除所有版块
2. MINOR LEVEL10
- Section Delete 可强制删除版块
"""

