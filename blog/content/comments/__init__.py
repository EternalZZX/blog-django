#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@apiDefine COMMENT_SELECT
评论查询权限
1. MAJOR LEVEL10
- Comment List 可自定义搜索查询
2. MAJOR LEVEL2
- Comment List 可模糊搜索查询
3. MAJOR LEVEL1
- Comment List 可精确搜索查询
4. MINOR LEVEL10
- Comment List 可自定义排序查询
5. MINOR LEVEL1
- Comment List 可排序查询
"""

"""
@apiDefine COMMENT_CREATE
评论创建权限
- 评论创建权限
"""

"""
@apiDefine COMMENT_PERMISSION
评论越权权限
1. MAJOR LEVEL10
- Comment Get    可查看所有状态评论
- Comment List   可查看所有状态评论
"""

"""
@apiDefine COMMENT_AUDIT
评论审核权限
1. MAJOR LEVEL10
- Comment Get    可查看审核状态评论
- Comment List   可查看审核状态评论
- Comment Get    可查看审核未通过状态评论
- Comment List   可查看审核未通过状态评论
2. MINOR LEVEL10
- Comment Create 可创建评论为审核状态
- Comment Update 可修改评论为审核状态
- Comment Create 可创建评论为审核通过状态
- Comment Update 可修改评论为审核通过状态
- Comment Create 可创建评论为审核未通过状态
- Comment Update 可修改评论为审核未通过状态
"""

"""
@apiDefine COMMENT_CANCEL
评论注销权限
1. MAJOR LEVEL10
- Comment Get    可查看注销状态评论
- Comment List   可查看注销状态评论
2. MINOR LEVEL10
- Comment Update 可修改评论为注销状态
- Comment Delete 可修改评论为注销状态
3. MINOR LEVEL1
- Comment Update 可修改自身评论为注销状态
- Comment Delete 可修改自身评论为注销状态
"""

"""
@apiDefine ARTICLE_UPDATE
评论编辑权限
1. MAJOR LEVEL10
- Comment Update 可编辑所有评论
1. MAJOR LEVEL1
- Comment Update 可编辑自身评论
"""

"""
@apiDefine ARTICLE_DELETE
评论删除权限
1. MAJOR LEVEL10
- Comment Delete 可删除所有评论
1. MAJOR LEVEL1
- Comment Delete 可删除自身评论
"""