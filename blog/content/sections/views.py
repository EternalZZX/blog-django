#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import QueryDict

from blog.content.sections.services import SectionService
from blog.common.message import ErrorMsg
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
    @apiPermission SECTION_PERMISSION
    @apiUse Header
    @apiSuccess {string} data 版块信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "status": 0,
            "description": null,
            "roles": [],
            "permission": {
                "set_permission": 0,
                "set_name": 0,
                "set_description": 2,
                "set_read_level": 1,
                "cancel_visible": 0,
                "delete_permission": 0,
                "set_status": 1,
                "set_assistant": 1,
                "set_moderator": 1,
                "set_nick": 2,
                "set_cancel": 1,
                "set_owner": 0,
                "set_read_user": 1
            },
            "read_permission": true,
            "read_level": 0,
            "create_at": "2018-01-26T06:02:52Z",
            "nick": "Test",
            "moderators": [],
            "only_groups": false,
            "owner": {
                "remark": null,
                "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                "create_at": "2017-12-20T11:19:17Z",
                "nick": "admin",
                "role": 1,
                "groups": []
            },
            "assistants": [],
            "only_roles": false,
            "groups": [],
            "id": 15,
            "name": "test"
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
    @apiPermission SECTION_PERMISSION
    @apiUse Header
    @apiParam {number} [page=0] 版块信息列表页码, 页码为0时返回所有数据
    @apiParam {number} [page_size=10] 版块信息列表页长
    @apiParam {string} [order_field] 版块信息列表排序字段
    @apiParam {string=desc, asc} [order="desc"] 版块信息列表排序方向
    @apiParam {string} [query] 搜索内容，若无搜索字段则全局搜索name, nick, description
    @apiParam {string=name, nick, DjangoFilterParams} [query_field] 搜索字段, 支持Django filter参数
    @apiSuccess {String} total 版块信息列表总数
    @apiSuccess {String} sections 版块信息列表
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "total": 1,
            "sections": [
                {
                    "status": 1,
                    "description": null,
                    "roles": [],
                    "read_level": 0,
                    "create_at": "2018-01-18T08:26:26Z",
                    "nick": "Python",
                    "moderators": [
                        {
                            "nick": "admin",
                            "remark": null,
                            "role": 1,
                            "create_at": "2017-12-20T11:19:17Z",
                            "groups": null
                        }
                    ],
                    "rw_permission": true,
                    "only_groups": false,
                    "assistants": [
                        {
                            "nick": "test",
                            "remark": null,
                            "role": 2,
                            "create_at": "2017-12-20T06:00:07Z",
                            "groups": null
                        }
                    ],
                    "only_roles": false,
                    "groups": [],
                    "id": 6,
                    "name": "python"
                }
            ]
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 403 Forbidden
    {
        "data": "Query permission denied"
    }
    """
    page = request.GET.get('page')
    page_size = request.GET.get('page_size')
    order_field = request.GET.get('order_field')
    order = request.GET.get('order')
    query = request.GET.get('query')
    query_field = request.GET.get('query_field')
    try:
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
    @apiParam {string} [cover_uuid] 版块封面UUID
    @apiParam {string} [owner_uuid={self}] 大版主UUID
    @apiParam {string} [moderator_uuids] 版主UUID列表，e.g.'7357d28a-a611-5efd-ae6e-a550a5b95487'
    @apiParam {string} [assistant_uuids] 副版主UUID列表，e.g.'4be0643f-1d98-573b-97cd-ca98a65347dd'
    @apiParam {number=0, 1, 2} [status=2] 版块状态, Cancel=0, Normal=1, Hide=2
    @apiParam {number} [read_level=0] 版块需求等级
    @apiParam {only_roles=true, false} [default=false] 是否指定角色拥有阅读权限
    @apiParam {string} [role_ids] 角色ID列表，e.g.'1;2'
    @apiParam {only_groups=true, false} [default=false] 是否指定组拥有阅读权限
    @apiParam {string} [group_ids] 用户组ID列表，e.g.'2;9;32;43'
    @apiParam {number=0, 1, 2, 3} [kwargs] 权限设置, Owner=0, Moderator=1, Manager=2, All=3,
                                           参数名'set_permission', 'delete_permission', 'set_owner',
                                           'set_name', 'set_nick', 'set_description', 'set_cover',
                                           'set_moderator', 'set_assistant', 'set_status',
                                           'set_cancel', 'cancel_visible', 'set_read_level',
                                           'set_read_user'，
                                           策略设置, 参数名'auto_audit', 'article_mute', 'reply_mute',
                                           'max_articles', 'max_articles_one_day'
    @apiSuccess {string} data 创建版块信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "status": 2,
            "policy": {
                "max_articles_one_day": null,
                "max_articles": null,
                "article_mute": false,
                "auto_audit": false,
                "reply_mute": false
            },
            "description": null,
            "roles": [],
            "permission": {
                "set_cover": 1,
                "set_description": 2,
                "article_edit": 2,
                "set_moderator": 1,
                "set_cancel": 1,
                "set_permission": 0,
                "cancel_visible": 2,
                "set_status": 1,
                "set_assistant": 1,
                "article_delete": 1,
                "set_read_level": 1,
                "article_draft": 1,
                "set_read_user": 1,
                "article_audit": 2,
                "set_name": 0,
                "set_policy": 1,
                "article_cancel": 2,
                "delete_permission": 0,
                "set_nick": 2,
                "article_recycled": 1,
                "set_owner": 0
            },
            "read_level": 0,
            "cover": "/media/photos/9b19df9b-25f5-5a09-a4ce-b7e0149699dc.jpeg",
            "create_at": "2018-01-26T10:17:05Z",
            "nick": "Test",
            "moderators": [
                {
                    "remark": null,
                    "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                    "create_at": "2017-12-20T11:19:17Z",
                    "nick": "admin",
                    "role": 1,
                    "avatar": "/media/photos/9b19df9b-25f5-5a09-a4ce-b7e0149699dc.jpeg",
                    "groups": null
                }
            ],
            "only_groups": false,
            "owner": {
                "remark": null,
                "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                "create_at": "2017-12-20T11:19:17Z",
                "nick": "admin",
                "role": 1,
                "avatar": "/media/photos/9b19df9b-25f5-5a09-a4ce-b7e0149699dc.jpeg",
                "groups": []
            },
            "assistants": [
                {
                    "remark": null,
                    "uuid": "4be0643f-1d98-573b-97cd-ca98a65347dd",
                    "create_at": "2017-12-20T06:00:07Z",
                    "nick": "test",
                    "role": 2,
                    "avatar": null,
                    "groups": null
                }
            ],
            "only_roles": false,
            "groups": [],
            "id": 18,
            "name": "test"
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
    cover_uuid = request.POST.get('cover_uuid')
    owner_uuid = request.POST.get('owner_uuid')
    moderator_uuids = request.POST.get('moderator_uuids')
    assistant_uuids = request.POST.get('assistant_uuids')
    status = request.POST.get('status')
    read_level = request.POST.get('read_level')
    only_roles = request.POST.get('only_roles') == 'true'
    role_ids = request.POST.get('role_ids')
    only_groups = request.POST.get('only_groups') == 'true'
    group_ids = request.POST.get('group_ids')
    kwargs = {}
    for key in (SectionService.SECTION_POLICY_FIELD + SectionService.SECTION_PERMISSION_FIELD):
        value = request.POST.get(key)
        if value is not None:
            kwargs[key] = value
    try:
        moderator_uuids = str_to_list(moderator_uuids)
        assistant_uuids = str_to_list(assistant_uuids)
        role_ids = str_to_list(role_ids)
        group_ids = str_to_list(group_ids)
        code, data = SectionService(request).create(name=name,
                                                    nick=nick,
                                                    description=description,
                                                    cover_uuid=cover_uuid,
                                                    owner_uuid=owner_uuid,
                                                    moderator_uuids=moderator_uuids,
                                                    assistant_uuids=assistant_uuids,
                                                    status=status,
                                                    read_level=read_level,
                                                    only_roles=only_roles,
                                                    role_ids=role_ids,
                                                    only_groups=only_groups,
                                                    group_ids=group_ids, **kwargs)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def section_update(request, section_id):
    """
    @api {put} /content/sections/{id}/ section update
    @apiVersion 0.1.0
    @apiName section_update
    @apiGroup content
    @apiDescription 编辑版块
    @apiPermission SECTION_UPDATE
    @apiUse Header
    @apiParam {string} name 版块名
    @apiParam {string} [nick={name}] 版块昵称
    @apiParam {string} [description] 版块描述
    @apiParam {string} [cover_uuid] 版块封面UUID
    @apiParam {string} [owner_uuid={self}] 大版主UUID
    @apiParam {string} [moderator_uuids] 版主UUID列表，e.g.'7357d28a-a611-5efd-ae6e-a550a5b95487'
    @apiParam {string} [assistant_uuids] 副版主UUID列表，e.g.'4be0643f-1d98-573b-97cd-ca98a65347dd'
    @apiParam {number=0, 1, 2} [status=2] 版块状态, Cancel=0, Normal=1, Hide=2
    @apiParam {number} [read_level=0] 版块需求等级
    @apiParam {only_roles=true, false} [default=false] 是否指定角色拥有阅读权限
    @apiParam {string} [role_ids] 角色ID列表，e.g.'1;2'
    @apiParam {only_groups=true, false} [default=false] 是否指定组拥有阅读权限
    @apiParam {string} [group_ids] 用户组ID列表，e.g.'2;9;32;43'
    @apiParam {number=0, 1, 2, 3} [kwargs] 权限设置, Owner=0, Moderator=1, Manager=2, All=3,
                                           参数名'set_permission', 'delete_permission', 'set_owner',
                                           'set_name', 'set_nick', 'set_description', 'set_cover',
                                           'set_moderator', 'set_assistant', 'set_status',
                                           'set_cancel', 'cancel_visible', 'set_read_level',
                                           'set_read_user'，
                                           策略设置, 参数名'auto_audit', 'article_mute', 'reply_mute',
                                           'max_articles', 'max_articles_one_day'
    @apiSuccess {string} data 编辑版块信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "status": 2,
            "policy": {
                "max_articles_one_day": null,
                "max_articles": null,
                "article_mute": false,
                "auto_audit": false,
                "reply_mute": false
            },
            "description": null,
            "roles": [],
            "permission": {
                "set_cover": 1,
                "set_description": 2,
                "article_edit": 2,
                "set_moderator": 1,
                "set_cancel": 1,
                "set_permission": 0,
                "cancel_visible": 2,
                "set_status": 1,
                "set_assistant": 1,
                "article_delete": 1,
                "set_read_level": 1,
                "article_draft": 1,
                "set_read_user": 1,
                "article_audit": 2,
                "set_name": 0,
                "set_policy": 1,
                "article_cancel": 2,
                "delete_permission": 0,
                "set_nick": 2,
                "article_recycled": 1,
                "set_owner": 0
            },
            "read_level": 0,
            "cover": "/media/photos/9b19df9b-25f5-5a09-a4ce-b7e0149699dc.jpeg",
            "create_at": "2018-01-26T10:17:05Z",
            "nick": "Test",
            "moderators": [
                {
                    "remark": null,
                    "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                    "create_at": "2017-12-20T11:19:17Z",
                    "nick": "admin",
                    "role": 1,
                    "avatar": "/media/photos/9b19df9b-25f5-5a09-a4ce-b7e0149699dc.jpeg",
                    "groups": null
                }
            ],
            "only_groups": false,
            "owner": {
                "remark": null,
                "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                "create_at": "2017-12-20T11:19:17Z",
                "nick": "admin",
                "role": 1,
                "avatar": "/media/photos/9b19df9b-25f5-5a09-a4ce-b7e0149699dc.jpeg",
                "groups": []
            },
            "assistants": [
                {
                    "remark": null,
                    "uuid": "4be0643f-1d98-573b-97cd-ca98a65347dd",
                    "create_at": "2017-12-20T06:00:07Z",
                    "nick": "test",
                    "role": 2,
                    "avatar": null,
                    "groups": null
                }
            ],
            "only_roles": false,
            "groups": [],
            "id": 18,
            "name": "test"
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 404 Not Found
    {
        "data": "Section not found"
    }
    """
    data = QueryDict(request.body)
    name = data.get('name')
    nick = data.get('nick')
    description = data.get('description')
    cover_uuid = data.get('cover_uuid')
    owner_uuid = data.get('owner_uuid')
    moderator_uuids = data.get('moderator_uuids')
    assistant_uuids = data.get('assistant_uuids')
    status = data.get('status')
    read_level = data.get('read_level')
    only_roles = data.get('only_roles')
    role_ids = data.get('role_ids')
    only_groups = data.get('only_groups')
    group_ids = data.get('group_ids')
    kwargs = {}
    for key in (SectionService.SECTION_POLICY_FIELD + SectionService.SECTION_PERMISSION_FIELD):
        value = data.get(key)
        if value is not None:
            kwargs[key] = value
    try:
        if only_roles is not None:
            only_roles = only_roles == 'true'
        if only_groups is not None:
            only_groups = only_groups == 'true'
        if moderator_uuids is not None:
            moderator_uuids = str_to_list(moderator_uuids)
        if assistant_uuids is not None:
            assistant_uuids = str_to_list(assistant_uuids)
        if role_ids is not None:
            role_ids = str_to_list(role_ids)
        if group_ids is not None:
            group_ids = str_to_list(group_ids)
        code, data = SectionService(request).update(section_id=section_id,
                                                    name=name,
                                                    nick=nick,
                                                    description=description,
                                                    cover_uuid=cover_uuid,
                                                    owner_uuid=owner_uuid,
                                                    moderator_uuids=moderator_uuids,
                                                    assistant_uuids=assistant_uuids,
                                                    status=status, read_level=read_level,
                                                    only_roles=only_roles,
                                                    role_ids=role_ids,
                                                    only_groups=only_groups,
                                                    group_ids=group_ids, **kwargs)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def section_delete(request, section_id):
    """
    @api {delete} /content/sections/[id]/ section delete
    @apiVersion 0.1.0
    @apiName section_delete
    @apiGroup content
    @apiDescription 删除版块
    @apiPermission SECTION_DELETE
    @apiUse Header
    @apiParam {string} [id_list] 删除版块id列表，e.g.'7;8;9', 当使用URL参数id时
                                 该参数忽略
    @apiParam {bool=true, false} [force=false] 强制删除
    @apiSuccess {string} data 版块删除信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "status": "SUCCESS",
                "id": "9",
                "name": "test"
            }
        ]
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 403 Forbidden
    {
        "data": "Permission denied"
    }
    """
    data = QueryDict(request.body)
    force = data.get('force') == 'true'
    try:
        if section_id:
            id_list = [{'delete_id': section_id, 'force': force}]
        else:
            id_list = data.get('id_list')
            if not isinstance(id_list, (unicode, str)):
                raise ParamsError()
            id_list = [{'delete_id': delete_id, 'force': force} for delete_id in id_list.split(';') if delete_id]
        code, data = 400, map(lambda params: SectionService(request).delete(**params), id_list)
        for result in data:
            if result['status'] == 'SUCCESS':
                code = 200
                break
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)
