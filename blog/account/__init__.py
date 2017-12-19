#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@apiDefine USER_SELECT
用户查询权限
1. MAJOR LEVEL10
- User Get 可获取注销用户
- User List 可获取注销用户
2. MAJOR LEVEL9
- User Get 可获取私有字段
- User List 可获取私有字段
- User List 可精确搜索私有字段
3. MAJOR LEVEL2
- User List 可模糊搜索公有字段
4. MAJOR LEVEL1
- User List 可精确搜索公有字段
5. MINOR LEVEL10
- User List 可排序私有字段
6. MINOR LEVEL1
- User List 可排序公有字段
"""

"""
@apiDefine USER_CREATE
用户创建权限
1. MAJOR LEVEL10
- User Create 可创建大于自身角色权限的用户
"""

"""
@apiDefine USER_UPDATE
用户编辑权限
1. MAJOR LEVEL10
- User Update 可编辑其他用户
- User Update 可编辑用户角色
- User Update 可编辑用户组
2. MINOR LEVEL10
- User Update 可修改其他用户密码无原密码
3. MINOR LEVEL9
- User Update 可修改其他用户密码
"""