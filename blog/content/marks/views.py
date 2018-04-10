#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import QueryDict

from blog.content.marks.services import MarkService
from blog.common.message import ErrorMsg
from blog.common.error import ParamsError
from blog.common.utils import Response, json_response, str_to_list


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
    pass


def mark_list(request):
    pass


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
    pass


def mark_delete(request, mark_uuid):
    pass
