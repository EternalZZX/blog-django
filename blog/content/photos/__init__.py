#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@apiDefine PHOTO_SELECT
照片查询权限
1. MAJOR LEVEL10
- Photo List 可自定义搜索查询
2. MAJOR LEVEL2
- Photo List 可模糊搜索查询
3. MAJOR LEVEL1
- Photo List 可精确搜索查询
4. MINOR LEVEL10
- Photo List 可自定义排序查询
5. MINOR LEVEL1
- Photo List 可排序查询
"""

"""
@apiDefine PHOTO_CREATE
照片创建权限
1. MAJOR LEVEL10
- Photo Create 可创建照片超过数量限制
2. VALUE
- Photo Create 创建照片数量限制
"""

"""
@apiDefine PHOTO_LIMIT
照片质量权限
1. MAJOR LEVEL10
- Photo Create 可创建照片保留原图尺寸
2. MINOR LEVEL10
- Photo Create 可创建照片保留原图文件
"""

"""
@apiDefine PHOTO_PERMISSION
照片越权权限
1. MAJOR LEVEL10
- Photo Get    可查看所有状态照片
- Photo List   可查看所有状态照片
"""

"""
@apiDefine PHOTO_AUDIT
照片审核权限
1. MAJOR LEVEL10
- Photo Get    可查看审核状态照片
- Photo List   可查看审核状态照片
- Photo Get    可查看审核未通过状态照片
- Photo List   可查看审核未通过状态照片
2. MINOR LEVEL10
- Photo Create 可创建照片为审核状态
- Photo Update 可修改照片为审核状态
- Photo Create 可创建照片为审核通过状态
- Photo Update 可修改照片为审核通过状态
- Photo Create 可创建照片为审核未通过状态
- Photo Update 可修改照片为审核未通过状态
"""

"""
@apiDefine PHOTO_CANCEL
照片注销权限
1. MAJOR LEVEL10
- Photo Get    可查看注销状态照片
- Photo List   可查看注销状态照片
2. MINOR LEVEL10
- Photo Update 可修改照片为注销状态
- Photo Delete 可修改照片为注销状态
3. MINOR LEVEL1
- Photo Update 可修改自身照片为注销状态
- Photo Delete 可修改自身照片为注销状态
"""

"""
@apiDefine PHOTO_PRIVACY
照片私有权限
1. MAJOR LEVEL10
- Photo Get    可查看非公有照片
- Photo List   可查看非公有照片
1. MINOR LEVEL2
- Photo Create 可创建照片为私有
- Photo Update 可修改照片为私有
2. MINOR LEVEL1
- Photo Create 可创建照片为受保护
- Photo Update 可修改照片为受保护
"""

"""
@apiDefine PHOTO_READ
照片阅读权限
1. MAJOR LEVEL10
- Photo Get    可查看任意阅读等级照片
- Photo List   可查看任意阅读等级照片
2. MINOR LEVEL10
- Photo Create 可创建照片为任意阅读等级
- Photo Update 可修改照片为任意阅读等级
3. MINOR LEVEL1
- Photo Create 可创建照片为小于等于自身的阅读等级
- Photo Update 可修改照片为小于等于自身的阅读等级
"""

"""
@apiDefine PHOTO_UPDATE
照片编辑权限
1. MAJOR LEVEL10
- Photo Update 可编辑所有照片
1. MAJOR LEVEL1
- Photo Update 可编辑自身照片
"""

"""
@apiDefine PHOTO_DELETE
照片删除权限
1. MAJOR LEVEL10
- Photo Delete 可删除所有照片
1. MAJOR LEVEL1
- Photo Delete 可删除自身照片
"""
