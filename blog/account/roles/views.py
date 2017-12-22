#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import QueryDict

from blog.account.roles.services import RoleService
from blog.common.message import ErrorMsg
from blog.common.setting import PermissionName
from blog.common.utils import Response, json_response


@json_response
def role_operate(request, role_id=None):
    if request.method == 'GET':
        if not role_id:
            response = role_list(request)
        else:
            response = role_get(request, role_id)
    elif request.method == 'POST':
        response = role_create(request)
    elif request.method == 'PUT':
        response = role_update(request, role_id)
    elif request.method == 'DELETE':
        response = role_delete(request, role_id)
    else:
        response = Response(code=405, data=ErrorMsg.REQUEST_METHOD_ERROR)
    return response


def role_get(request, role_id):
    """
    @api {get} /account/roles/{id}/ role get
    @apiVersion 0.1.0
    @apiName role_get
    @apiGroup account
    @apiDescription 获取角色信息详情
    @apiPermission ROLE_SELECT
    @apiUse Header
    @apiSuccess {string} data 角色信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "name": "admin",
            "default": false,
            "create_at": "2017-12-20T11:19:17Z",
            "role_level": 1000,
            "nick": "管理员",
            "id": 1,
            "permissions": [
                {
                    "status": true,
                    "description": null,
                    "name": "login",
                    "nick": "登陆权限",
                    "id": 1,
                    "major_level": 1000
                }
            ]
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 404 Not Found
    {
        "data": "Role not found"
    }
    """
    try:
        code, data = RoleService(request).get(role_id=role_id)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def role_list(request):
    """
        @api {get} /account/roles/ role list
        @apiVersion 0.1.0
        @apiName role_list
        @apiGroup account
        @apiDescription 获取角色信息列表
        @apiPermission ROLE_SELECT
        @apiUse Header
        @apiParam {number} [page=0] 角色信息列表页码, 页码为0时返回所有数据
        @apiParam {number} [page_size=10] 角色信息列表页长
        @apiParam {string} [order_field] 角色信息列表排序字段
        @apiParam {string=desc, asc} [order="desc"] 角色信息列表排序方向
        @apiParam {string} [query] 搜索内容，若无搜索字段则全局搜索name, nick
        @apiParam {string=name, nick, DjangoFilterParams} [query_field] 搜索字段, 支持Django filter参数
        @apiSuccess {String} total 角色信息列表总数
        @apiSuccess {String} roles 角色信息列表
        @apiSuccessExample {json} Success-Response:
        HTTP/1.1 200 OK
        {
            "data": {
                "total": 3,
                "roles": [
                    {
                        "name": "admin",
                        "default": false,
                        "create_at": "2017-12-20T11:19:17Z",
                        "role_level": 1000,
                        "nick": "系统管理员",
                        "id": 1,
                        "permissions": [
                            {
                                "status": true,
                                "description": null,
                                "name": "login",
                                "nick": "登陆权限",
                                "id": 1,
                                "major_level": 1000
                            }
                        ]
                    }
                ]
            }
        }
        @apiUse ErrorData
        @apiErrorExample {json} Error-Response:
        HTTP/1.1 403 Forbidden
        {
            "data": "Order field permission denied"
        }
        """
    try:
        page = request.GET.get('page')
        page_size = request.GET.get('page_size')
        order_field = request.GET.get('order_field')
        order = request.GET.get('order')
        query = request.GET.get('query')
        query_field = request.GET.get('query_field')
        code, data = RoleService(request).list(page=page,
                                               page_size=page_size,
                                               order_field=order_field,
                                               order=order,
                                               query=query,
                                               query_field=query_field)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def role_create(request):
    """
    @api {post} /account/roles/ role create
    @apiVersion 0.1.0
    @apiName role_create
    @apiGroup account
    @apiDescription 创建角色
    @apiPermission ROLE_CREATE
    @apiUse Header
    @apiParam {string} name 角色名
    @apiParam {string} [nick={name}] 角色昵称
    @apiParam {number} [role_level=0] 角色等级
    @apiParam {string=true, false} [default=false] 是否用户默认角色
    @apiParam {string} [kwargs] 权限设置, e.g. '{"state": "true", "major_level": 100,
                                "minor_level": 100, "value": 3}', 参数名为权限名称,
                                e.g."create_user"
    @apiSuccess {string} data 创建角色信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "name": "op",
            "default": true,
            "create_at": "2017-12-21T06:51:16.626Z",
            "role_level": 900,
            "nick": "管理员",
            "id": 24,
            "permissions": [
                {
                    "status": true,
                    "nick": "用户创建权限",
                    "description": "",
                    "major_level": 900,
                    "id": 30,
                    "name": "user_create"
                }
            ]
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 400 Bad Request
    {
        "data": "Duplicate identity field"
    }
    """
    name = request.POST.get('name')
    nick = request.POST.get('nick')
    role_level = request.POST.get('role_level')
    default = request.POST.get('default') == 'true'
    kwargs = {}
    for k, v in PermissionName():
        json_str = request.POST.get(v)
        if json_str:
            kwargs[v] = json_str
    try:
        code, data = RoleService(request).create(name=name,
                                                 nick=nick,
                                                 role_level=role_level,
                                                 default=default,
                                                 **kwargs)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def role_update(request, role_id):
    """
    @api {put} /account/roles/{id}/ role update
    @apiVersion 0.1.0
    @apiName role_update
    @apiGroup account
    @apiDescription 编辑角色
    @apiPermission ROLE_UPDATE
    @apiUse Header
    @apiParam {string} name 角色名
    @apiParam {string} [nick={name}] 角色昵称
    @apiParam {number} [role_level=0] 角色等级
    @apiParam {string=true, false} [default=false] 是否用户默认角色
    @apiParam {string} [kwargs] 权限设置, e.g. '{"state": "true", "major_level": 100,
                                "minor_level": 100, "value": 3}', 参数名为权限名称,
                                e.g."create_user"
    @apiSuccess {string} data 编辑用户信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "name": "op",
            "default": false,
            "create_at": "2017-12-22T02:59:50Z",
            "role_level": 900,
            "nick": "管理员",
            "id": 25,
            "permissions": [
                {
                    "status": true,
                    "description": null,
                    "name": "login",
                    "nick": "登陆权限",
                    "id": 32,
                    "major_level": 1000
                }
            ]
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 404 Not Found
    {
        "data": "Role not found"
    }
    """
    data = QueryDict(request.body)
    name = data.get('name')
    nick = data.get('nick')
    role_level = data.get('role_level')
    default = data.get('default')
    kwargs = {}
    for k, v in PermissionName():
        json_str = data.get(v)
        if json_str:
            kwargs[v] = json_str
    try:
        if default is not None:
            default = default == 'true'
        code, data = RoleService(request).update(role_id=role_id,
                                                 name=name,
                                                 nick=nick,
                                                 role_level=role_level,
                                                 default=default,
                                                 **kwargs)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def role_delete(request, role_id):
    return Response(code=200, data={})
