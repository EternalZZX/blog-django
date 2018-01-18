#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import QueryDict

from blog.content.sections.services import SectionService
from blog.common.message import ErrorMsg
from blog.common.setting import PermissionName
from blog.common.error import ParamsError
from blog.common.utils import Response, json_response, str_to_list


@json_response
def section_operate(request, section_id=None):
    if request.method == 'GET':
        if not section_id:
            response = section_list(request)
        else:
            response = section_get(request, section_id)
    elif request.method == 'POST':
        response = section_create(request)
    elif request.method == 'PUT':
        response = section_update(request, section_id)
    elif request.method == 'DELETE':
        response = section_delete(request, section_id)
    else:
        response = Response(code=405, data=ErrorMsg.REQUEST_METHOD_ERROR)
    return response


def section_get(request, section_id):
    """
    @api {get} /content/sections/{id}/ section get
    @apiVersion 0.1.0
    @apiName section_get
    @apiGroup content
    @apiDescription 获取版块信息详情
    @apiPermission SECTION_SELECT
    @apiUse Header
    @apiSuccess {string} data 版块信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "status": 2,
            "description": null,
            "roles": [
                1,
                2
            ],
            "level": 0,
            "nick": "JavaScript",
            "moderators": [
                {
                    "nick": "test",
                    "remark": null,
                    "role": 2,
                    "create_at": "2017-12-20T06:00:07Z",
                    "groups": null
                }
            ],
            "only_groups": false,
            "assistants": [],
            "only_roles": false,
            "groups": [],
            "id": 5,
            "name": "javascript"
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 404 Not Found
    {
        "data": "Section not found"
    }
    """
    try:
        code, data = SectionService(request).get(section_id=section_id)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def section_list(request):
    """
    @api {get} /content/sections/ section list
    @apiVersion 0.1.0
    @apiName section_list
    @apiGroup content
    @apiDescription 获取版块信息列表
    @apiPermission SECTION_SELECT
    @apiUse Header
    @apiParam {number} [page=0] 版块信息列表页码, 页码为0时返回所有数据
    @apiParam {number} [page_size=10] 版块信息列表页长
    @apiParam {string} [order_field] 版块信息列表排序字段
    @apiParam {string=desc, asc} [order="desc"] 版块信息列表排序方向
    @apiParam {string} [query] 搜索内容，若无搜索字段则全局搜索name, nick, description
    @apiParam {string=name, nick, DjangoFilterParams} [query_field] 搜索字段, 支持Django filter参数
    @apiSuccess {String} total 版块信息列表总数
    @apiSuccess {String} roles 版块信息列表
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
        code, data = SectionService(request).list(page=page,
                                                  page_size=page_size,
                                                  order_field=order_field,
                                                  order=order,
                                                  query=query,
                                                  query_field=query_field)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def section_create(request):
    """
    @api {post} /content/sections/ section create
    @apiVersion 0.1.0
    @apiName section_create
    @apiGroup content
    @apiDescription 创建版块
    @apiPermission SECTION_CREATE
    @apiUse Header
    @apiParam {string} name 版块名
    @apiParam {string} [nick={name}] 版块昵称
    @apiParam {string} [description] 版块描述
    @apiParam {string} [moderator_uuids] 版主UUID列表，e.g.'7357d28a-a611-5efd-ae6e-a550a5b95487'
    @apiParam {string} [assistant_uuids] 副版主UUID列表，e.g.'4be0643f-1d98-573b-97cd-ca98a65347dd'
    @apiParam {number=0, 1, 2} [status=2] 版块状态, Cancel=0, Visible_only=1, Active=2
    @apiParam {number} [level=0] 版块需求等级
    @apiParam {only_roles=true, false} [default=false] 是否指定角色拥有阅读权限
    @apiParam {string} [role_ids] 角色ID列表，e.g.'1;2'
    @apiParam {only_groups=true, false} [default=false] 是否指定组拥有阅读权限
    @apiParam {string} [group_ids] 用户组ID列表，e.g.'2;9;32;43'
    @apiSuccess {string} data 创建版块信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "status": 2,
            "description": null,
            "roles": [],
            "level": 0,
            "nick": "JavaScript",
            "moderators": [
                "7357d28a-a611-5efd-ae6e-a550a5b95487"
            ],
            "only_groups": false,
            "assistants": [
                "4be0643f-1d98-573b-97cd-ca98a65347dd"
            ],
            "only_roles": false,
            "groups": [],
            "id": 4,
            "name": "javascript"
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
    description = request.POST.get('description')
    moderator_uuids = request.POST.get('moderator_uuids')
    assistant_uuids = request.POST.get('assistant_uuids')
    status = request.POST.get('status')
    level = request.POST.get('level')
    only_roles = request.POST.get('only_roles') == 'true'
    role_ids = request.POST.get('role_ids')
    only_groups = request.POST.get('only_groups') == 'true'
    group_ids = request.POST.get('group_ids')
    try:
        moderator_uuids = str_to_list(moderator_uuids)
        assistant_uuids = str_to_list(assistant_uuids)
        role_ids = str_to_list(role_ids)
        group_ids = str_to_list(group_ids)
        code, data = SectionService(request).create(name=name,
                                                    nick=nick,
                                                    description=description,
                                                    moderator_uuids=moderator_uuids,
                                                    assistant_uuids=assistant_uuids,
                                                    status=status,
                                                    level=level,
                                                    only_roles=only_roles,
                                                    role_ids=role_ids,
                                                    only_groups=only_groups,
                                                    group_ids=group_ids)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def section_update(request, section_id):
    pass


def section_delete(request, section_id):
    pass
