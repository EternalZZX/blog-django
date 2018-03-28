#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import QueryDict

from blog.content.comments.services import CommentService
from blog.common.message import ErrorMsg
from blog.common.error import ParamsError
from blog.common.utils import Response, json_response


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
    @apiUse Header
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
                "avatar": "/media/photos/7357d28a-a611-5efd-ae6e-a550a5b95487/small/9b19df9b-25f5-5a09-a4ce-b7e0149699dc.jpeg",
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
    try:
        code, data = CommentService(request).get(comment_uuid=comment_uuid)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def comment_list(request):
    pass


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
                "avatar": "/media/photos/7357d28a-a611-5efd-ae6e-a550a5b95487/small/9b19df9b-25f5-5a09-a4ce-b7e0149699dc.jpeg",
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
    resource_type = request.POST.get('resource_type')
    resource_uuid = request.POST.get('resource_uuid')
    reply_uuid = request.POST.get('reply_uuid')
    content = request.POST.get('content')
    status = request.POST.get('status')
    try:
        code, data = CommentService(request).create(resource_type=resource_type,
                                                    resource_uuid=resource_uuid,
                                                    reply_uuid=reply_uuid,
                                                    content=content,
                                                    status=status)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def comment_update(request, comment_uuid):
    pass


def comment_delete(request, comment_uuid):
    pass
