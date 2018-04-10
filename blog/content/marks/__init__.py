#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@apiDefine MARK_SELECT
标签查询权限
1. MAJOR LEVEL10
- Mark List 可自定义搜索查询
2. MAJOR LEVEL2
- Mark List 可模糊搜索查询
3. MAJOR LEVEL1
- Mark List 可精确搜索查询
4. MINOR LEVEL10
- Mark List 可自定义排序查询
5. MINOR LEVEL1
- Mark List 可排序查询
"""

"""
@apiDefine MARK_CREATE
标签创建权限
1. MAJOR LEVEL10
- Mark Create 可创建相册为其他作者
"""

"""
@apiDefine MARK_UPDATE
标签编辑权限
1. MAJOR LEVEL10
- Mark Update 可编辑所有标签
2. MINOR LEVEL10
- Mark Update 可编辑标签为其他作者
"""

"""
@apiDefine MARK_DELETE
标签删除权限
1. MAJOR LEVEL10
- Mark Delete 可删除所有标签
2. MAJOR LEVEL1
- Mark Delete 可删除自身标签
"""

"""
@apiDefine MARK_PRIVACY
标签私有权限
1. MAJOR LEVEL10
- Mark Get    可查看非公有标签
- Mark List   可查看非公有标签
2. MINOR LEVEL1
- Mark Create 可创建标签为私有
- Mark Update 可修改标签为私有
"""