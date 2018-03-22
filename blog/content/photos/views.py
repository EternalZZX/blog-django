#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import QueryDict
from django.http import HttpResponse, JsonResponse

from blog.content.photos.services import PhotoService
from blog.common.message import ErrorMsg
from blog.common.error import ParamsError
from blog.common.utils import Response, json_response
from blog.common.setting import AuthType


def photo_show(request):
    try:
        code, data = PhotoService(request, auth_type=AuthType.COOKIE).show(request.path)
        return HttpResponse(data, content_type="image/png")
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return JsonResponse({'data': data}, status=code)


@json_response
def photo_operate(request, photo_uuid=None):
    if request.method == 'GET':
        if not photo_uuid:
            response = photo_list(request)
        else:
            response = photo_get(request, photo_uuid)
    elif request.method == 'POST':
        response = photo_create(request)
    elif request.method == 'PUT':
        response = photo_update(request, photo_uuid)
    elif request.method == 'DELETE':
        response = photo_delete(request, photo_uuid)
    else:
        response = Response(code=405, data=ErrorMsg.REQUEST_METHOD_ERROR)
    return response


def photo_get(request, photo_uuid):
    """
    @api {get} /content/photos/{uuid}/ photo get
    @apiVersion 0.1.0
    @apiName photo_get
    @apiGroup content
    @apiDescription 获取照片信息详情
    @apiPermission PHOTO_SELECT
    @apiPermission PHOTO_PERMISSION
    @apiPermission PHOTO_PRIVACY
    @apiPermission PHOTO_READ
    @apiPermission PHOTO_CANCEL
    @apiPermission PHOTO_AUDIT
    @apiUse Header
    @apiSuccess {string} data 照片信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "image_large": null,
            "album": 1,
            "uuid": "f94a8727-7b6f-5c36-a554-022f3cb54baa",
            "author": {
                "remark": null,
                "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                "create_at": "2017-12-20T11:19:17Z",
                "nick": "admin",
                "role": 1,
                "groups": []
            },
            "read_level": 100,
            "privacy": 1,
            "image_small": null,
            "image_middle": null,
            "image_untreated": null,
            "dislike_count": 0,
            "create_at": "2018-03-19T09:10:39Z",
            "like_count": 0,
            "status": 1,
            "id": 44,
            "description": "test album"
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 404 Not Found
    {
        "data": "Photo not found"
    }
    """
    try:
        code, data = PhotoService(request).get(photo_uuid=photo_uuid)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def photo_list(request):
    """
    @api {get} /content/photos/ photo list
    @apiVersion 0.1.0
    @apiName photo_list
    @apiGroup content
    @apiDescription 获取照片信息列表
    @apiPermission PHOTO_SELECT
    @apiPermission PHOTO_PERMISSION
    @apiPermission PHOTO_PRIVACY
    @apiPermission PHOTO_READ
    @apiPermission PHOTO_CANCEL
    @apiPermission PHOTO_AUDIT
    @apiUse Header
    @apiParam {number} [page=0] 照片信息列表页码, 页码为0时返回所有数据
    @apiParam {number} [page_size=10] 照片信息列表页长
    @apiParam {string} [album_uuid] 照片所属相册
    @apiParam {string} [author_uuid] 照片作者
    @apiParam {string=0, 1, 2, 3, 4, 5} [status] 照片状态，Cancel=0, Active=1, Audit=2,
                                                 Failed=3, Recycled=4，状态可拼接，e.g. '123'
    @apiParam {string} [order_field] 照片信息列表排序字段
    @apiParam {string=desc, asc} [order="desc"] 照片信息列表排序方向
    @apiParam {string} [query] 搜索内容，若无搜索字段则全局搜索description, author, album
    @apiParam {string=name, nick, DjangoFilterParams} [query_field] 搜索字段, 支持Django filter参数
    @apiSuccess {String} total 照片信息列表总数
    @apiSuccess {String} photos 照片信息列表
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "photos": [
                {
                    "image_large": null,
                    "album": 1,
                    "uuid": "f94a8727-7b6f-5c36-a554-022f3cb54baa",
                    "author": {
                        "remark": null,
                        "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                        "create_at": "2017-12-20T11:19:17Z",
                        "nick": "admin",
                        "role": 1,
                        "groups": []
                    },
                    "read_level": 100,
                    "privacy": 1,
                    "image_small": null,
                    "image_middle": null,
                    "image_untreated": null,
                    "dislike_count": 0,
                    "create_at": "2018-03-19T09:10:39Z",
                    "like_count": 0,
                    "status": 1,
                    "id": 44,
                    "description": "test album"
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
    album_uuid = request.GET.get('album_uuid')
    author_uuid = request.GET.get('author_uuid')
    status = request.GET.get('status')
    order_field = request.GET.get('order_field')
    order = request.GET.get('order')
    query = request.GET.get('query')
    query_field = request.GET.get('query_field')
    try:
        code, data = PhotoService(request).list(page=page,
                                                page_size=page_size,
                                                album_uuid=album_uuid,
                                                author_uuid=author_uuid,
                                                status=status,
                                                order_field=order_field,
                                                order=order,
                                                query=query,
                                                query_field=query_field)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def photo_create(request):
    """
    @api {post} /content/photos/ photo create
    @apiVersion 0.1.0
    @apiName photo_create
    @apiGroup content
    @apiDescription 创建照片
    @apiPermission PHOTO_CREATE
    @apiPermission PHOTO_PRIVACY
    @apiPermission PHOTO_READ
    @apiPermission PHOTO_CANCEL
    @apiPermission PHOTO_AUDIT
    @apiUse Header
    @apiParam {file} image 照片文件
    @apiParam {string} description 照片描述
    @apiParam {string} [album_uuid] 照片所属相册UUID
    @apiParam {number=0, 1, 2, 3, 4, 5} [status=1] 照片状态, Cancel=0, Active=1, Audit=2,
                                                   Failed=3, Recycled=4
    @apiParam {number=0, 1, 2} [privacy=1] 照片私有状态, Private=0, Public=1, Protected=2
    @apiParam {number} [read_level=100] 照片需求阅读等级
    @apiParam {bool=true, false} [origin=false] 保留原图尺寸
    @apiParam {bool=true, false} [untreated=false] 保留原图文件
    @apiSuccess {string} data 创建照片信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "image_large": "/media/photos/7357d28a-a611-5efd-ae6e-a550a5b95487.jpeg",
            "album": 1,
            "uuid": "2a14706b-ca65-5af6-b234-001ab1c52f76",
            "author": {
                "remark": null,
                "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                "create_at": "2017-12-20T11:19:17Z",
                "nick": "admin",
                "role": 1,
                "groups": []
            },
            "read_level": 100,
            "privacy": 1,
            "image_small": "/media/photos/7357d28a-a611-5efd-ae6e-a550a5b95487.jpeg",
            "image_middle": "/media/photos/7357d28a-a611-5efd-ae6e-a550a5b95487.jpeg",
            "image_untreated": "/media/photos/7357d28a-a611-5efd-ae6e-a550a5b95487.jpg",
            "dislike_count": 0,
            "create_at": "2018-03-20T10:36:19.767Z",
            "like_count": 0,
            "status": 1,
            "id": 60,
            "description": "test album"
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 403 Forbidden
    {
        "data": "Album permission denied"
    }
    """
    image = request.FILES.get('image')
    description = request.POST.get('description')
    album_uuid = request.POST.get('album_uuid')
    status = request.POST.get('status')
    privacy = request.POST.get('privacy')
    read_level = request.POST.get('read_level')
    origin = request.POST.get('origin') == 'true'
    untreated = request.POST.get('untreated') == 'true'
    try:
        code, data = PhotoService(request).create(image=image,
                                                  description=description,
                                                  album_uuid=album_uuid,
                                                  status=status,
                                                  privacy=privacy,
                                                  read_level=read_level,
                                                  origin=origin,
                                                  untreated=untreated)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def photo_update(request, photo_uuid):
    """
    @api {put} /content/photos/{uuid}/ photo update
    @apiVersion 0.1.0
    @apiName photo_update
    @apiGroup content
    @apiDescription 编辑照片
    @apiPermission PHOTO_UPDATE
    @apiPermission PHOTO_PRIVACY
    @apiPermission PHOTO_READ
    @apiPermission PHOTO_CANCEL
    @apiPermission PHOTO_AUDIT
    @apiUse Header
    @apiParam {string} description 照片描述
    @apiParam {string} [album_uuid] 照片所属相册UUID
    @apiParam {number=0, 1, 2, 3, 4, 5} [status=1] 照片状态, Cancel=0, Active=1, Audit=2,
                                                   Failed=3, Recycled=4
    @apiParam {number=0, 1, 2} [privacy=1] 照片私有状态, Private=0, Public=1, Protected=2
    @apiParam {number} [read_level=100] 照片需求阅读等级
    @apiParam {number} [like_count=1] 文章点赞
    @apiParam {number} [dislike_count=1] 文章取消点赞
    @apiSuccess {string} data 编辑照片信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "image_large": null,
            "album": 1,
            "edit_at": "2018-03-22T02:26:09.768Z",
            "uuid": "f94a8727-7b6f-5c36-a554-022f3cb54baa",
            "author": {
                "remark": null,
                "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                "create_at": "2017-12-20T11:19:17Z",
                "nick": "admin",
                "role": 1,
                "groups": []
            },
            "read_level": 100,
            "privacy": 1,
            "image_small": null,
            "image_middle": null,
            "image_untreated": null,
            "dislike_count": 0,
            "create_at": "2018-03-19T09:10:39Z",
            "like_count": 0,
            "status": 1,
            "last_editor": {
                "remark": null,
                "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                "create_at": "2017-12-20T11:19:17Z",
                "nick": "admin",
                "role": 1,
                "groups": []
            },
            "id": 44,
            "description": "album"
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
    description = data.get('description')
    album_uuid = data.get('album_uuid')
    status = data.get('status')
    privacy = data.get('privacy')
    read_level = data.get('read_level')
    like_count = data.get('like_count')
    dislike_count = data.get('dislike_count')
    try:
        code, data = PhotoService(request).update(photo_uuid=photo_uuid,
                                                  description=description,
                                                  album_uuid=album_uuid,
                                                  status=status,
                                                  privacy=privacy,
                                                  read_level=read_level,
                                                  like_count=like_count,
                                                  dislike_count=dislike_count)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def photo_delete(request, photo_uuid):
    data = QueryDict(request.body)
    force = data.get('force') == 'true'
    try:
        if photo_uuid:
            id_list = [{'delete_id': photo_uuid, 'force': force}]
        else:
            id_list = data.get('id_list')
            if not isinstance(id_list, (unicode, str)):
                raise ParamsError()
            id_list = [{'delete_id': delete_id, 'force': force} for delete_id in id_list.split(';') if delete_id]
        code, data = 400, map(lambda params: PhotoService(request).delete(**params), id_list)
        for result in data:
            if result['status'] == 'SUCCESS':
                code = 200
                break
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)
