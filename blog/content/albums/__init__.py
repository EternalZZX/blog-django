#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@apiDefine ALBUM_SELECT
相册查询权限
1. MAJOR LEVEL10
- Album List 可自定义搜索查询
2. MAJOR LEVEL2
- Album List 可模糊搜索查询
3. MAJOR LEVEL1
- Album List 可精确搜索查询
4. MINOR LEVEL10
- Album List 可自定义排序查询
5. MINOR LEVEL1
- Album List 可排序查询
"""

"""
@apiDefine ALBUM_CREATE
相册创建权限
1. MAJOR LEVEL10
- Album Create 可创建相册为其他作者
"""

"""
@apiDefine ALBUM_UPDATE
相册编辑权限
1. MAJOR LEVEL10
- Album Update 可编辑所有相册
- Photo Create 可为所有相册添加照片
- Photo Update 可为所有相册编辑照片
- Photo Delete 可为所有相册删除照片
2. MINOR LEVEL10
- Album Update 可编辑相册为其他作者
"""

"""
@apiDefine ALBUM_DELETE
相册删除权限
1. MAJOR LEVEL10
- Album Delete 可删除所有相册
2. MAJOR LEVEL1
- Album Delete 可删除自身相册
"""

"""
@apiDefine ALBUM_PRIVACY
相册私有权限
1. MAJOR LEVEL10
- Album Get    可查看非公有相册
- Album List   可查看非公有相册
2. MINOR LEVEL2
- Album Create 可创建相册为私有
- Album Update 可修改相册为私有
3. MINOR LEVEL1
- Album Create 可创建相册为受保护
- Album Update 可修改相册为受保护
"""

"""
@apiDefine ALBUM_SYSTEM
相册系统权限
1. MAJOR LEVEL10
- Album Create 可创建相册为系统相册
- Album Update 可编辑相册为系统相册
"""