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
    """
    @api {get} /content/albums/ album list
    @apiVersion 0.1.0
    @apiName album_list
    @apiGroup content
    @apiDescription 获取相册信息列表
    @apiPermission ALBUM_SELECT
    @apiPermission ALBUM_PRIVACY
    @apiUse Header
    @apiParam {number} [page=0] 相册信息列表页码, 页码为0时返回所有数据
    @apiParam {number} [page_size=10] 相册信息列表页长
    @apiParam {string} [author_uuid] 相册作者
    @apiParam {string} [order_field] 相册信息列表排序字段
    @apiParam {string=desc, asc} [order="desc"] 相册信息列表排序方向
    @apiParam {string} [query] 搜索内容，若无搜索字段则全局搜索name, description, author
    @apiParam {string=name, description, author, DjangoFilterParams} [query_field] 搜索字段, 支持Django filter参数
    @apiSuccess {String} total 相册信息列表总数
    @apiSuccess {String} albums 相册信息列表
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "albums": [
                {
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
            ],
            "total": 1
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
    order_field = request.GET.get('order_field')
    order = request.GET.get('order')
    query = request.GET.get('query')
    query_field = request.GET.get('query_field')
    try:
        code, data = AlbumService(request).list(page=page,
                                                page_size=page_size,
                                                author_uuid=author_uuid,
                                                order_field=order_field,
                                                order=order,
                                                query=query,
                                                query_field=query_field)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


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
    """
    @api {put} /content/albums/{uuid}/ album update
    @apiVersion 0.1.0
    @apiName album_update
    @apiGroup content
    @apiDescription 编辑相册
    @apiPermission ALBUM_UPDATE
    @apiPermission ALBUM_PRIVACY
    @apiUse Header
    @apiParam {string} name 相册名
    @apiParam {string} [description] 相册描述
    @apiParam {string} [author_uuid={self}] 作者UUID
    @apiParam {number=0, 1, 2} [privacy=1] 相册私有状态, Private=0, Public=1, Protected=2
    @apiSuccess {string} data 编辑相册信息详情
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
            "name": "album"
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
    author_uuid = data.get('author_uuid')
    privacy = data.get('privacy')
    try:
        code, data = AlbumService(request).update(album_uuid=album_uuid,
                                                  name=name,
                                                  description=description,
                                                  author_uuid=author_uuid,
                                                  privacy=privacy)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def album_delete(request, album_uuid):
    """
    @api {delete} /content/albums/[uuid]/ album delete
    @apiVersion 0.1.0
    @apiName album_delete
    @apiGroup content
    @apiDescription 删除相册
    @apiPermission ALBUM_DELETE
    @apiUse Header
    @apiParam {string} [id_list] 删除相册uuid列表，e.g.'11d9fc3a-051f-5271-b1e1-65c192b63105;',
                                 当使用URL参数uuid时该参数忽略
    @apiSuccess {string} data 相册删除信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "status": "SUCCESS",
                "nick": "test-album",
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
        if album_uuid:
            id_list = [{'delete_id': album_uuid}]
        else:
            id_list = data.get('id_list')
            if not isinstance(id_list, (unicode, str)):
                raise ParamsError()
            id_list = [{'delete_id': delete_id} for delete_id in id_list.split(';') if delete_id]
        code, data = 400, map(lambda params: AlbumService(request).delete(**params), id_list)
        for result in data:
            if result['status'] == 'SUCCESS':
                code = 200
                break
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)
