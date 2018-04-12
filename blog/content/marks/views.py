#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import QueryDict

from blog.content.marks.services import MarkService
from blog.common.message import ErrorMsg
from blog.common.error import ParamsError
from blog.common.utils import Response, json_response


@json_response
def mark_operate(request, mark_uuid=None):
    if request.method == 'GET':
        if not mark_uuid:
            response = mark_list(request)
        else:
            response = mark_get(request, mark_uuid)
    elif request.method == 'POST':
        response = mark_create(request)
    elif request.method == 'PUT':
        response = mark_update(request, mark_uuid)
    elif request.method == 'DELETE':
        response = mark_delete(request, mark_uuid)
    else:
        response = Response(code=405, data=ErrorMsg.REQUEST_METHOD_ERROR)
    return response


def mark_get(request, mark_uuid):
    """
    @api {get} /content/marks/{uuid}/ mark get
    @apiVersion 0.1.0
    @apiName mark_get
    @apiGroup content
    @apiDescription 获取标签信息详情
    @apiPermission MARK_SELECT
    @apiPermission MARK_PRIVACY
    @apiUse Header
    @apiSuccess {string} data 标签信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "attach_count": 1,
            "description": "description",
            "author": {
                "remark": null,
                "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                "create_at": "2017-12-20T11:19:17Z",
                "nick": "admin",
                "role": 1,
                "avatar": "/media/photos/9b19df9b-25f5-5a09-a4ce-b7e0149699dc.jpeg",
                "groups": []
            },
            "color": "#ffffff",
            "privacy": 1,
            "uuid": "b9751e9d-ec9b-5f9a-a382-c656af9ce2b4",
            "create_at": "2018-04-11T07:08:21Z",
            "id": 4,
            "resources": [
                {
                    "resource_type": 0,
                    "resource_uuid": "6623d8a4-55b0-5d9f-8623-5ff5e1d8ce09"
                }
            ],
            "name": "test"
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 404 Not Found
    {
        "data": "Mark not found"
    }
    """
    try:
        code, data = MarkService(request).get(mark_uuid=mark_uuid)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def mark_list(request):
    """
    @api {get} /content/marks/ mark list
    @apiVersion 0.1.0
    @apiName mark_list
    @apiGroup content
    @apiDescription 获取标签信息列表
    @apiPermission MARK_SELECT
    @apiPermission MARK_PRIVACY
    @apiUse Header
    @apiParam {number} [page=0] 标签信息列表页码, 页码为0时返回所有数据
    @apiParam {number} [page_size=10] 标签信息列表页长
    @apiParam {string} [author_uuid] 标签作者UUID
    @apiParam {number=0, 1, 2} [resource_type] 标签绑定资源类型，Article=0, Album=1, Photo=2
    @apiParam {string} [resource_uuid] 标签绑定资源UUID
    @apiParam {string} [order_field] 标签信息列表排序字段
    @apiParam {string=desc, asc} [order="desc"] 标签信息列表排序方向
    @apiParam {string} [query] 搜索内容，若无搜索字段则全局搜索uuid, name, description, author, color
    @apiParam {string=uuid, name, description, author, color, DjangoFilterParams} [query_field]
                               搜索字段, 支持Django filter参数
    @apiSuccess {String} total 标签信息列表总数
    @apiSuccess {String} marks 标签信息列表
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "total": 1,
            "marks": [
                {
                    "attach_count": 1,
                    "description": "description",
                    "author": {
                        "remark": null,
                        "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                        "create_at": "2017-12-20T11:19:17Z",
                        "nick": "admin",
                        "role": 1,
                        "avatar": "/media/photos/9b19df9b-25f5-5a09-a4ce-b7e0149699dc.jpeg",
                        "groups": []
                    },
                    "color": "#ffffff",
                    "privacy": 1,
                    "uuid": "d2336aba-5129-5b6b-9d94-fc3744bed04c",
                    "create_at": "2018-04-11T07:01:15Z",
                    "id": 3,
                    "name": "test"
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
    author_uuid = request.GET.get('author_uuid')
    resource_type = request.GET.get('resource_type')
    resource_uuid = request.GET.get('resource_uuid')
    order_field = request.GET.get('order_field')
    order = request.GET.get('order')
    query = request.GET.get('query')
    query_field = request.GET.get('query_field')
    try:
        code, data = MarkService(request).list(page=page,
                                               page_size=page_size,
                                               author_uuid=author_uuid,
                                               resource_type=resource_type,
                                               resource_uuid=resource_uuid,
                                               order_field=order_field,
                                               order=order,
                                               query=query,
                                               query_field=query_field)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def mark_create(request):
    """
    @api {post} /content/marks/ mark create
    @apiVersion 0.1.0
    @apiName mark_create
    @apiGroup content
    @apiDescription 创建标签
    @apiPermission MARK_CREATE
    @apiPermission MARK_PRIVACY
    @apiUse Header
    @apiParam {string} name 标签名
    @apiParam {string} [description] 标签描述
    @apiParam {string} [color] 标签颜色
    @apiParam {number=0, 1} [privacy=1] 标签私有状态, Private=0, Public=1
    @apiParam {string} [author_uuid={self}] 作者UUID
    @apiParam {number=0, 1, 2} [resource_type] 标签绑定资源类型, Article=0, Album=1, Photo=2
    @apiParam {string} [resource_uuid] 标签绑定资源UUID
    @apiSuccess {string} data 创建标签信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "attach_count": 0,
            "description": "description",
            "author": {
                "remark": null,
                "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                "create_at": "2017-12-20T11:19:17Z",
                "nick": "admin",
                "role": 1,
                "avatar": "/media/photos/7357d28a-a611-5efd-ae6e-a550a5b95487.jpeg",
                "groups": []
            },
            "color": "#ffffff",
            "privacy": 1,
            "uuid": "da56f4a8-1cef-5dbe-ade8-bfc615c0dbd5",
            "create_at": "2018-04-10T06:55:23.422Z",
            "id": 2,
            "name": "test"
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 403 Forbidden
    {
        "data": "Permission denied"
    }
    """
    name = request.POST.get('name')
    description = request.POST.get('description')
    color = request.POST.get('color')
    privacy = request.POST.get('privacy')
    author_uuid = request.POST.get('author_uuid')
    resource_type = request.POST.get('resource_type')
    resource_uuid = request.POST.get('resource_uuid')
    try:
        code, data = MarkService(request).create(name=name,
                                                 description=description,
                                                 color=color,
                                                 privacy=privacy,
                                                 author_uuid=author_uuid,
                                                 resource_type=resource_type,
                                                 resource_uuid=resource_uuid)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def mark_update(request, mark_uuid):
    """
    @api {put} /content/marks/{uuid}/ mark update
    @apiVersion 0.1.0
    @apiName mark_update
    @apiGroup content
    @apiDescription 编辑标签
    @apiPermission MARK_UPDATE
    @apiPermission MARK_PRIVACY
    @apiUse Header
    @apiParam {string} name 标签名
    @apiParam {string} [description] 标签描述
    @apiParam {string} [color] 标签颜色
    @apiParam {number=0, 1} [privacy=1] 标签私有状态, Private=0, Public=1
    @apiParam {string} [author_uuid={self}] 作者UUID
    @apiParam {number=0, 1} [operate] 绑定解绑标签操作, Attach=1, Detach=0
    @apiParam {number=0, 1, 2} [resource_type] 标签绑定解绑资源类型, Article=0, Album=1, Photo=2
    @apiParam {string} [resource_uuid] 标签绑定解绑资源UUID
    @apiSuccess {string} data 编辑标签信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "attach_count": 1,
            "description": "description",
            "author": {
                "remark": null,
                "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                "create_at": "2017-12-20T11:19:17Z",
                "nick": "admin",
                "role": 1,
                "avatar": "/media/photos/9b19df9b-25f5-5a09-a4ce-b7e0149699dc.jpeg",
                "groups": []
            },
            "color": "#ffffff",
            "privacy": 1,
            "uuid": "d2336aba-5129-5b6b-9d94-fc3744bed04c",
            "create_at": "2018-04-11T07:01:15Z",
            "id": 3,
            "resources": [
                {
                    "resource_type": 0,
                    "resource_uuid": "6623d8a4-55b0-5d9f-8623-5ff5e1d8ce09"
                }
            ],
            "name": "mark"
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 403 Forbidden
    {
        "data": "Permission denied"
    }
    """
    data = QueryDict(request.body)
    name = data.get('name')
    description = data.get('description')
    color = data.get('color')
    privacy = data.get('privacy')
    author_uuid = data.get('author_uuid')
    operate = data.get('operate')
    resource_type = data.get('resource_type')
    resource_uuid = data.get('resource_uuid')
    try:
        code, data = MarkService(request).update(mark_uuid=mark_uuid,
                                                 name=name,
                                                 description=description,
                                                 color=color,
                                                 privacy=privacy,
                                                 author_uuid=author_uuid,
                                                 operate=operate,
                                                 resource_type=resource_type,
                                                 resource_uuid=resource_uuid)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def mark_delete(request, mark_uuid):
    """
    @api {delete} /content/marks/[uuid]/ mark delete
    @apiVersion 0.1.0
    @apiName mark_delete
    @apiGroup content
    @apiDescription 删除标签
    @apiPermission MARK_DELETE
    @apiUse Header
    @apiParam {string} [id_list] 删除标签uuid列表，e.g.'11d9fc3a-051f-5271-b1e1-65c192b63105,',
                                 当使用URL参数uuid时该参数忽略
    @apiSuccess {string} data 标签删除信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "status": "SUCCESS",
                "name": "test",
                "id": "174a7ba6-0a15-5402-b827-d3e670218d5b"
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
    try:
        if mark_uuid:
            id_list = [{'delete_id': mark_uuid}]
        else:
            id_list = data.get('id_list')
            if not isinstance(id_list, (unicode, str)):
                raise ParamsError()
            id_list = [{'delete_id': delete_id} for delete_id in id_list.split(',') if delete_id]
        code, data = 400, map(lambda params: MarkService(request).delete(**params), id_list)
        for result in data:
            if result['status'] == 'SUCCESS':
                code = 200
                break
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)
