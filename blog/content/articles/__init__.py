#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@apiDefine ARTICLE_SELECT
文章查询权限
1. MAJOR LEVEL10
- Article List 可自定义搜索查询
2. MAJOR LEVEL2
- Article List 可模糊搜索查询
3. MAJOR LEVEL1
- Article List 可精确搜索查询
4. MINOR LEVEL10
- Article List 可自定义排序查询
5. MINOR LEVEL1
- Article List 可排序查询
"""

"""
@apiDefine ARTICLE_CREATE
文章创建权限
- 文章创建权限
"""

"""
@apiDefine ARTICLE_PERMISSION
文章越权权限
1. MAJOR LEVEL10
- Article Get    可查看所有状态文章
- Article List   可查看所有状态文章
"""

"""
@apiDefine ARTICLE_AUDIT
文章审核权限
1. MAJOR LEVEL10
- Article Get    可查看审核状态文章
- Article List   可查看审核状态文章
- Article Get    可查看审核未通过状态文章
- Article List   可查看审核未通过状态文章
2. MINOR LEVEL10
- Article Create 可创建文章为审核状态
- Article Update 可修改文章为审核状态
- Article Create 可创建文章为审核通过状态
- Article Update 可修改文章为审核通过状态
- Article Create 可创建文章为审核未通过状态
- Article Update 可修改文章为审核未通过状态
"""

"""
@apiDefine ARTICLE_CANCEL
文章注销权限
1. MAJOR LEVEL10
- Article Get    可查看注销状态文章
- Article List   可查看注销状态文章
2. MINOR LEVEL10
- Article Update 可修改文章为注销状态
- Article Delete 可修改文章为注销状态
3. MINOR LEVEL1
- Article Update 可修改自身文章为注销状态
- Article Delete 可修改自身文章为注销状态
"""

"""
@apiDefine ARTICLE_PRIVACY
文章私有权限
1. MAJOR LEVEL10
- Article Get    可查看非公有文章
- Article List   可查看非公有文章
1. MINOR LEVEL2
- Article Create 可创建文章为私有
- Article Update 可修改文章为私有
2. MINOR LEVEL1
- Article Create 可创建文章为受保护
- Article Update 可修改文章为受保护
"""

"""
@apiDefine ARTICLE_READ
文章阅读权限
1. MAJOR LEVEL10
- Article Get    可查看任意阅读等级文章
- Article List   可查看任意阅读等级文章
2. MINOR LEVEL10
- Article Create 可创建文章为任意阅读等级
- Article Update 可修改文章为任意阅读等级
3. MINOR LEVEL1
- Article Create 可创建文章为小于等于自身的阅读等级
- Article Update 可修改文章为小于等于自身的阅读等级
"""

"""
@apiDefine ARTICLE_UPDATE
文章编辑权限
1. MAJOR LEVEL10
- Article Update 可编辑所有文章
1. MAJOR LEVEL1
- Article Update 可编辑自身文章
"""

"""
@apiDefine ARTICLE_DELETE
文章删除权限
1. MAJOR LEVEL10
- Article Delete 可删除所有文章
1. MAJOR LEVEL1
- Article Delete 可删除自身文章
"""