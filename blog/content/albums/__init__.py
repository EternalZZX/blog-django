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
2. MAJOR LEVEL1
- Album Update 可编辑自身相册
3. MINOR LEVEL10
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