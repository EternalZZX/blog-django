#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import QueryDict

from blog.content.comments.services import CommentService
from blog.common.message import ErrorMsg
from blog.common.error import ParamsError
from blog.common.utils import Response, json_response, request_parser


@json_response
def comment_operate(request, comment_uuid=None):
    if request.method == 'GET':
        if not comment_uuid:
            response = comment_list(request)
        else:
            response = comment_get(request, comment_uuid)
    elif request.method == 'POST':
        response = comment_create(request)
    elif request.method == 'PUT':
        response = comment_update(request, comment_uuid)
    elif request.method == 'DELETE':
        response = comment_delete(request, comment_uuid)
    else:
        response = Response(code=405, data=ErrorMsg.REQUEST_METHOD_ERROR)
    return response


def comment_get(request, comment_uuid):
    """
    @api {get} /content/comments/{uuid}/ comment get
    @apiVersion 0.1.0
    @apiName comment_get
    @apiGroup content
    @apiDescription 获取评论信息详情
    @apiPermission COMMENT_SELECT
    @apiPermission COMMENT_PERMISSION
    @apiPermission COMMENT_CANCEL
    @apiPermission COMMENT_AUDIT
    @apiPermission COMMENT_LIKE
    @apiUse Header
    @apiParam {number=1, 2, 3} [like_list_type] 查看点赞列表类型, Like=1, Dislike=2, All=3
    @apiParam {number} [like_list_start=0] 查看点赞用户列表起始下标
    @apiParam {number} [like_list_end=10] 查看点赞用户列表结束下标, -1时返回所有数据
    @apiSuccess {string} data 评论信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "resource_section": 18,
            "reply_user": {
                "remark": null,
                "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                "create_at": "2017-12-20T11:19:17Z",
                "nick": "admin",
                "role": 1,
                "avatar": "/media/photos/9b19df9b-25f5-5a09-a4ce-b7e0149699dc.jpeg",
                "groups": []
            },
            "edit_at": "2018-03-27T08:49:22Z",
            "uuid": "9b3629e8-3f13-56cb-b6fc-3e5f22799bd5",
            "author": {
                "remark": null,
                "uuid": "4be0643f-1d98-573b-97cd-ca98a65347dd",
                "create_at": "2017-12-20T06:00:07Z",
                "nick": "test",
                "role": 2,
                "avatar": null,
                "groups": []
            },
            "dislike_count": 0,
            "create_at": "2018-03-27T09:07:52Z",
            "resource_uuid": "11d9fc3a-051f-5271-b1e1-65c192b63105",
            "content": "content...",
            "resource_author": 1,
            "like_count": 0,
            "status": 1,
            "last_editor": {
                "remark": null,
                "uuid": "4be0643f-1d98-573b-97cd-ca98a65347dd",
                "create_at": "2017-12-20T06:00:07Z",
                "nick": "test",
                "role": 2,
                "avatar": null,
                "groups": []
            },
            "id": 10,
            "resource_type": 0,
            "parent_uuid": "40905eb5-02c3-5951-bdc4-0274ff78bd3c"
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 404 Not Found
    {
        "data": "Comment not found"
    }
    """
    params = {
        'like_list_type': int,
        'like_list_start': int,
        'like_list_end': int
    }
    try:
        params_dict = request_parser(data=request.GET, params=params)
        code, data = CommentService(request).get(comment_uuid=comment_uuid,
                                                 **params_dict)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def comment_list(request):
    """
    @api {get} /content/comments/ comment list
    @apiVersion 0.1.0
    @apiName comment_list
    @apiGroup content
    @apiDescription 获取评论信息列表
    @apiPermission COMMENT_SELECT
    @apiPermission COMMENT_PERMISSION
    @apiPermission COMMENT_CANCEL
    @apiPermission COMMENT_AUDIT
    @apiUse Header
    @apiParam {number} [page=0] 评论信息列表页码, 页码为0时返回所有数据
    @apiParam {number} [page_size=10] 文评论信息列表页长
    @apiParam {number=0, 1, 2} [resource_type] 评论资源类型，Article=0, Album=1, Photo=2
    @apiParam {string} [resource_uuid] 评论资源UUID
    @apiParam {number} [resource_section_id] 评论资源所属板块
    @apiParam {string} [dialog_uuid] 对话评论UUID
    @apiParam {string} [reply_uuid] 回复评论UUID
    @apiParam {string} [author_uuid] 评论作者
    @apiParam {number=0, 1, 2, 3, 4} [status] 评论状态，Cancel=0, Active=1, Audit=2,
                                              Failed=3, Recycled=4，状态可拼接，e.g. '123'
    @apiParam {string} [order_field] 评论信息列表排序字段
    @apiParam {string=desc, asc} [order="desc"] 评论信息列表排序方向
    @apiParam {string} [query] 搜索内容，若无搜索字段则全局搜索content, author
    @apiParam {string=uuid, content, author, status, DjangoFilterParams} [query_field] 搜索字段, 支持Django filter参数
    @apiSuccess {String} total 评论信息列表总数
    @apiSuccess {String} comments 评论信息列表
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "total": 1,
            "comments": [
                {
                    "resource_section": 18,
                    "reply_user": null,
                    "edit_at": "2018-03-27T07:14:24Z",
                    "uuid": "d6fe0af9-90a1-566b-822a-af304f40ee4c",
                    "author": {
                        "remark": null,
                        "uuid": "4be0643f-1d98-573b-97cd-ca98a65347dd",
                        "create_at": "2017-12-20T06:00:07Z",
                        "nick": "test",
                        "role": 2,
                        "avatar": null,
                        "groups": []
                    },
                    "dislike_count": 0,
                    "create_at": "2018-03-27T07:53:41Z",
                    "resource_uuid": "11d9fc3a-051f-5271-b1e1-65c192b63105",
                    "content": "content...",
                    "resource_author": 1,
                    "like_count": 0,
                    "status": 1,
                    "last_editor": {
                        "remark": null,
                        "uuid": "4be0643f-1d98-573b-97cd-ca98a65347dd",
                        "create_at": "2017-12-20T06:00:07Z",
                        "nick": "test",
                        "role": 2,
                        "avatar": null,
                        "groups": []
                    },
                    "id": 4,
                    "resource_type": 0,
                    "parent_uuid": null
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
    params = {
        'page': int,
        'page_size': int,
        'resource_type': int,
        'resource_uuid': str,
        'resource_section_id': int,
        'dialog_uuid': str,
        'reply_uuid': str,
        'author_uuid': str,
        'status': str,
        'order_field': str,
        'order': str,
        'query': str,
        'query_field': str
    }
    try:
        params_dict = request_parser(data=request.GET, params=params)
        code, data = CommentService(request).list(**params_dict)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def comment_create(request):
    """
    @api {post} /content/comments/ comment create
    @apiVersion 0.1.0
    @apiName comment_create
    @apiGroup content
    @apiDescription 创建评论
    @apiPermission COMMENT_CREATE
    @apiPermission COMMENT_CANCEL
    @apiPermission COMMENT_AUDIT
    @apiUse Header
    @apiParam {number=0, 1, 2} resource_type 评论资源类型, Article=0, Album=1, Photo=2
    @apiParam {string} resource_uuid 评论资源UUID
    @apiParam {string} [reply_uuid] 回复评论UUID
    @apiParam {string} [content] 评论内容
    @apiParam {number=0, 1, 2, 3, 4} [status=1] 评论状态, Cancel=0, Active=1, Audit=2,
                                                   Failed=3, Recycled=4
    @apiSuccess {string} data 创建评论信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "resource_section": 18,
            "reply_user": {
                "remark": null,
                "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                "create_at": "2017-12-20T11:19:17Z",
                "nick": "admin",
                "role": 1,
                "avatar": "/media/photos/9b19df9b-25f5-5a09-a4ce-b7e0149699dc.jpeg",
                "groups": []
            },
            "edit_at": "2018-03-27T08:49:22.637Z",
            "uuid": "9b3629e8-3f13-56cb-b6fc-3e5f22799bd5",
            "author": {
                "remark": null,
                "uuid": "4be0643f-1d98-573b-97cd-ca98a65347dd",
                "create_at": "2017-12-20T06:00:07Z",
                "nick": "test",
                "role": 2,
                "avatar": null,
                "groups": []
            },
            "dislike_count": 0,
            "create_at": "2018-03-27T09:07:52.801Z",
            "resource_uuid": "11d9fc3a-051f-5271-b1e1-65c192b63105",
            "content": "content...",
            "resource_author": 1,
            "like_count": 0,
            "status": 1,
            "last_editor": {
                "remark": null,
                "uuid": "4be0643f-1d98-573b-97cd-ca98a65347dd",
                "create_at": "2017-12-20T06:00:07Z",
                "nick": "test",
                "role": 2,
                "avatar": null,
                "groups": []
            },
            "id": 10,
            "resource_type": 0,
            "parent_uuid": "40905eb5-02c3-5951-bdc4-0274ff78bd3c"
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 404 Not Found
    {
        "data": "Comment not found"
    }
    """
    params = {
        'resource_type': int,
        'resource_uuid': str,
        'reply_uuid': str,
        'content': str,
        'status': int
    }
    try:
        params_dict = request_parser(data=request.POST, params=params)
        code, data = CommentService(request).create(**params_dict)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def comment_update(request, comment_uuid):
    """
    @api {put} /content/comments/{uuid}/ comment update
    @apiVersion 0.1.0
    @apiName comment_update
    @apiGroup content
    @apiDescription 编辑评论
    @apiPermission COMMENT_UPDATE
    @apiPermission COMMENT_CANCEL
    @apiPermission COMMENT_AUDIT
    @apiPermission COMMENT_LIKE
    @apiUse Header
    @apiParam {string} [content] 评论内容
    @apiParam {number=0, 1, 2, 3, 4} [status=1] 评论状态, Cancel=0, Active=1, Audit=2,
                                                Failed=3, Recycled=4
    @apiParam {number=0, 1} [like_operate] 评论点赞 Like=1, Dislike=0
    @apiSuccess {string} data 编辑评论信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "resource_section": 18,
            "reply_user": {
                "remark": null,
                "uuid": "4be0643f-1d98-573b-97cd-ca98a65347dd",
                "create_at": "2017-12-20T06:00:07Z",
                "nick": "test",
                "role": 2,
                "avatar": null,
                "groups": []
            },
            "edit_at": "2018-03-28T09:23:50.816Z",
            "uuid": "40905eb5-02c3-5951-bdc4-0274ff78bd3c",
            "author": {
                "remark": null,
                "uuid": "4be0643f-1d98-573b-97cd-ca98a65347dd",
                "create_at": "2017-12-20T06:00:07Z",
                "nick": "test",
                "role": 2,
                "avatar": null,
                "groups": []
            },
            "dislike_count": 0,
            "create_at": "2018-03-27T08:04:54Z",
            "resource_uuid": "11d9fc3a-051f-5271-b1e1-65c192b63105",
            "content": "test",
            "resource_author": 1,
            "like_count": 0,
            "status": 1,
            "last_editor": {
                "remark": null,
                "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                "create_at": "2017-12-20T11:19:17Z",
                "nick": "admin",
                "role": 1,
                "avatar": "/media/photos/9b19df9b-25f5-5a09-a4ce-b7e0149699dc.jpeg",
                "groups": []
            },
            "id": 7,
            "resource_type": 0,
            "parent_uuid": "b20db0ca-d448-567e-870d-a4f2f6607eec"
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 403 Forbidden
    {
        "data": "Permission denied"
    }
    """
    params = {
        'content': str,
        'status': int,
        'like_operate': int
    }
    try:
        body = QueryDict(request.body)
        params_dict = request_parser(data=body, params=params)
        code, data = CommentService(request).update(comment_uuid=comment_uuid,
                                                    **params_dict)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def comment_delete(request, comment_uuid):
    """
    @api {delete} /content/comments/[uuid]/ comment delete
    @apiVersion 0.1.0
    @apiName comment_delete
    @apiGroup content
    @apiDescription 删除评论
    @apiPermission COMMENT_DELETE
    @apiPermission COMMENT_CANCEL
    @apiUse Header
    @apiParam {string} [id_list] 删除评论uuid列表，e.g.'11d9fc3a-051f-5271-b1e1-65c192b63105,',
                                 当使用URL参数uuid时该参数忽略
    @apiParam {bool=true, false} [force=false] 强制删除
    @apiSuccess {string} data 评论删除信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "status": "SUCCESS",
                "id": "11d9fc3a-051f-5271-b1e1-65c192b63105",
                "name": "content..."
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
        if comment_uuid:
            id_list = [{'delete_id': comment_uuid, 'force': force}]
        else:
            id_list = data.get('id_list')
            if not isinstance(id_list, (unicode, str)):
                raise ParamsError()
            id_list = [{'delete_id': delete_id, 'force': force} for delete_id in id_list.split(',') if delete_id]
        code, data = 400, map(lambda params: CommentService(request).delete(**params), id_list)
        for result in data:
            if result['status'] == 'SUCCESS':
                code = 200
                break
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)
