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
@apiDefine ARTICLE_STATUS
文章状态权限
1. MAJOR LEVEL10
- User Create 可创建文章为审核通过状态
- User Update 可修改文章为审核通过状态
- User Create 可创建文章为审核未通过状态
- User Update 可修改文章为审核未通过状态
2. MINOR LEVEL10
- User Create 可创建文章为注销状态
- User Update 可修改所有文章为注销状态
- User Delete 可修改所有文章为注销状态
3. MINOR LEVEL1
- User Update 可修改自身文章为注销状态
- User Delete 可修改自身文章为注销状态
"""

"""
@apiDefine ARTICLE_PRIVACY
文章私有权限
1. MAJOR LEVEL2
- User Create 可创建文章为私有
- User Update 可修改文章为私有
2. MAJOR LEVEL1
- User Create 可创建文章为受保护
- User Update 可修改文章为受保护
3. MINOR LEVEL10
- User Create 可创建文章为任意阅读等级
- User Update 可修改文章为任意阅读等级
3. MINOR LEVEL1
- User Create 可创建文章为小于自身的阅读等级
- User Update 可修改文章为小于自身的阅读等级
"""

"""
@apiDefine ARTICLE_UPDATE
文章编辑权限
- 文章编辑权限
"""

"""
@apiDefine ARTICLE_DELETE
文章删除权限
- 文章删除权限
"""