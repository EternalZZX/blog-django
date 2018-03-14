#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@apiDefine ALBUM_CREATE
相册创建权限
1. MAJOR LEVEL10
- Album Create 可创建相册为其他作者
"""

"""
@apiDefine ALBUM_PRIVACY
相册私有权限
1. MAJOR LEVEL10
- Album Get    可查看非公有相册
- Album List   可查看非公有相册
1. MINOR LEVEL2
- Album Create 可创建相册为私有
- Album Update 可修改相册为私有
2. MINOR LEVEL1
- Album Create 可创建相册为受保护
- Album Update 可修改相册为受保护
"""