#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import QueryDict

from blog.content.albums.services import AlbumService
from blog.common.message import ErrorMsg
from blog.common.error import ParamsError
from blog.common.utils import Response, json_response, str_to_list


@json_response
def album_operate(request, album_uuid=None):
    if request.method == 'GET':
        if not album_uuid:
            response = album_list(request)
        else:
            response = album_get(request, album_uuid)
    elif request.method == 'POST':
        response = album_create(request)
    elif request.method == 'PUT':
        response = album_update(request, album_uuid)
    elif request.method == 'DELETE':
        response = album_delete(request, album_uuid)
    else:
        response = Response(code=405, data=ErrorMsg.REQUEST_METHOD_ERROR)
    return response


def album_get(request, album_uuid):
    """
    @api {get} /content/albums/{uuid}/ album get
    @apiVersion 0.1.0
    @apiName album_get
    @apiGroup content
    @apiDescription 获取相册信息详情
    @apiPermission ALBUM_SELECT
    @apiPermission ALBUM_PRIVACY
    @apiUse Header
    @apiSuccess {string} data 相册信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "description": "description",
            "privacy": 1,
            "author": {
                "remark": null,
                "uuid": "4be0643f-1d98-573b-97cd-ca98a65347dd",
                "create_at": "2017-12-20T06:00:07Z",
                "nick": "test",
                "role": 2,
                "groups": []
            },
            "uuid": "0c91df50-0709-574b-86c8-e867fb022521",
            "create_at": "2018-03-14T06:11:19Z",
            "id": 1,
            "name": "test-album"
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 404 Not Found
    {
        "data": "Album not found"
    }
    """
    try:
        code, data = AlbumService(request).get(album_uuid=album_uuid)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def album_list(request):
    pass


def album_create(request):
    """
    @api {post} /content/albums/ album create
    @apiVersion 0.1.0
    @apiName album_create
    @apiGroup content
    @apiDescription 创建相册
    @apiPermission ALBUM_CREATE
    @apiPermission ALBUM_PRIVACY
    @apiUse Header
    @apiParam {string} name 相册名
    @apiParam {string} [description] 相册描述
    @apiParam {string} [author_uuid={self}] 作者UUID
    @apiParam {number=0, 1, 2} [privacy=1] 相册私有状态, Private=0, Public=1, Protected=2
    @apiSuccess {string} data 创建相册信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "description": "description",
            "privacy": 1,
            "author": {
                "remark": null,
                "uuid": "4be0643f-1d98-573b-97cd-ca98a65347dd",
                "create_at": "2017-12-20T06:00:07Z",
                "nick": "test",
                "role": 2,
                "groups": []
            },
            "uuid": "174a7ba6-0a15-5402-b827-d3e670218d5b",
            "create_at": "2018-03-14T06:15:07.354Z",
            "id": 2,
            "name": "test-album"
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
    author_uuid = request.POST.get('author_uuid')
    privacy = request.POST.get('privacy')
    try:
        code, data = AlbumService(request).create(name=name,
                                                  description=description,
                                                  author_uuid=author_uuid,
                                                  privacy=privacy)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def album_update(request, album_uuid):
    pass


def album_delete(request, album_uuid):
    pass
