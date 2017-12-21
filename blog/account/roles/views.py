#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
    return Response(code=200, data={})


def role_list(request):
    return Response(code=200, data={})


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
    @apiParam {string} [nick={username}] 角色昵称
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
        kwargs[v] = request.POST.get(v)
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
    return Response(code=200, data={})


def role_delete(request, role_id):
    return Response(code=200, data={})
