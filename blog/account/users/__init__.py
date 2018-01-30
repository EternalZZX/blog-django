#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@apiDefine USER_SELECT
用户查询权限
1. MAJOR LEVEL10
- User List 可自定义搜索查询
2. MAJOR LEVEL2
- User List 可模糊搜索查询
3. MAJOR LEVEL1
- User List 可精确搜索查询
4. MINOR LEVEL10
- User List 可自定义排序查询
5. MINOR LEVEL1
- User List 可排序查询
"""

"""
@apiDefine USER_PRIVACY
用户隐私查询权限
1. MAJOR LEVEL10
- User Get  可获取其他用户隐私和管理字段
- User List 可获取其他用户隐私和管理字段
2. MAJOR LEVEL9
- User Get  可获取其他用户隐私字段
- User List 可获取其他用户隐私字段
"""

"""
@apiDefine USER_CREATE
用户创建权限
- User Create 用户创建权限
"""

"""
@apiDefine USER_STATUS
用户状态权限
1. MAJOR LEVEL10
- User Create 可创建用户为非激活状态
- User Update 可修改用户为非激活状态
"""

"""
@apiDefine USER_UPDATE
用户编辑权限
1. MAJOR LEVEL10
- User Update 可编辑所有用户
2. MAJOR LEVEL9
- User Update 可编辑小于自身角色权限的用户
3. MINOR LEVEL10
- User Update 可修改其他用户密码无原密码
4. MINOR LEVEL9
- User Update 可修改其他用户密码需原密码
"""


"""
@apiDefine USER_ROLE
用户角色权限
1. MAJOR LEVEL10
- User Update 可修改所有用户的角色
2. MAJOR LEVEL9
- User Update 可修改小于自身角色权限的其他用户的角色
4. MINOR LEVEL10
- User Create 可创建用户为任意角色
- User Update 可修改用户为任意角色
5. MINOR LEVEL9
- User Create 可创建用户为小于自身角色权限的角色
- User Update 可修改用户为小于自身角色权限的角色
"""

"""
@apiDefine USER_DELETE
用户删除权限
1. MAJOR LEVEL10
- User Delete 可删除所有用户
2. MAJOR LEVEL9
- User Delete 可删除小于自身角色权限的其他用户
3. MAJOR LEVEL1
- User Delete 可删除自身用户
"""

"""
@apiDefine USER_CANCEL
用户注销权限
1. MAJOR LEVEL10
- User Delete 可注销所有用户
2. MAJOR LEVEL9
- User Delete 可注销小于自身角色权限的其他用户
3. MAJOR LEVEL1
- User Delete 可注销自身用户
4. MINOR LEVEL10
- User Get    可获取注销用户
- User List   可获取注销用户
"""
