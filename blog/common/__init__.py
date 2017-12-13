#!/usr/bin/env python
# -*- coding: utf-8 -*-

from blog.common.setting import Setting

"""
@apiDefine Header
@apiHeader {String} [Auth-Token] 用户身份验证Token
"""

"""
@apiDefine ErrorData
@apiError {String} data 错误信息
"""

"""
@apiDefine USER_CREATE
用户创建权限
1. MAJOR LEVEL10
- User Create 可创建大于自身角色权限的用户
"""

"""
@apiDefine USER_SELECT
用户查询权限
1. MAJOR LEVEL10
- User Get 可获取私有字段
- User List 可获取私有字段
- User List 可精确搜索私有字段
2. MAJOR LEVEL2
- User List 可模糊搜索公有字段
3. MAJOR LEVEL1
- User List 可精确搜索公有字段
4. MINOR LEVEL10
- User List 可排序私有字段
5. MINOR LEVEL1
- User List 可排序公有字段
"""

Setting()
