#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import QueryDict

from blog.content.articles.services import ArticleService
from blog.common.message import ErrorMsg
from blog.common.error import ParamsError
from blog.common.utils import Response, json_response, request_parser


@json_response
def article_operate(request, article_uuid=None):
    if request.method == 'GET':
        if not article_uuid:
            response = article_list(request)
        else:
            response = article_get(request, article_uuid)
    elif request.method == 'POST':
        response = article_create(request)
    elif request.method == 'PUT':
        response = article_update(request, article_uuid)
    elif request.method == 'DELETE':
        response = article_delete(request, article_uuid)
    else:
        response = Response(code=405, data=ErrorMsg.REQUEST_METHOD_ERROR)
    return response


def article_get(request, article_uuid):
    """
    @api {get} /content/articles/{uuid}/ article get
    @apiVersion 0.1.0
    @apiName article_get
    @apiGroup content
    @apiDescription 获取文章信息详情
    @apiPermission ARTICLE_SELECT
    @apiPermission ARTICLE_PERMISSION
    @apiPermission ARTICLE_PRIVACY
    @apiPermission ARTICLE_READ
    @apiPermission ARTICLE_CANCEL
    @apiPermission ARTICLE_AUDIT
    @apiPermission ARTICLE_LIKE
    @apiUse Header
    @apiParam {number=1, 2, 3} [like_list_type] 查看点赞列表类型, Like=1, Dislike=2, All=3
    @apiParam {number} [like_list_start=0] 查看点赞用户列表起始下标
    @apiParam {number} [like_list_end=10] 查看点赞用户列表结束下标, -1时返回所有数据
    @apiSuccess {string} data 文章信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "status": 1,
            "dislike_count": 0,
            "edit_at": "2018-02-23T02:14:56Z",
            "uuid": "11d9fc3a-051f-5271-b1e1-65c192b63105",
            "title": "test-article",
            "read_level": 200,
            "section": 18,
            "author": {
                "remark": null,
                "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                "create_at": "2017-12-20T11:19:17Z",
                "nick": "admin",
                "role": 1,
                "groups": []
            },
            "create_at": "2018-02-23T02:25:47Z",
            "content_url": null,
            "content": "content...",
            "privacy": 1,
            "like_count": 0,
            "keywords": "keyword1,keyword2,",
            "id": 1
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 404 Not Found
    {
        "data": "Article not found"
    }
    """
    params = {
        'like_list_type': int,
        'like_list_start': int,
        'like_list_end': int
    }
    try:
        params_dict = request_parser(data=request.GET, params=params)
        code, data = ArticleService(request).get(article_uuid=article_uuid,
                                                 **params_dict)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def article_list(request):
    """
    @api {get} /content/articles/ article list
    @apiVersion 0.1.0
    @apiName article_list
    @apiGroup content
    @apiDescription 获取文章信息列表
    @apiPermission ARTICLE_SELECT
    @apiPermission ARTICLE_PERMISSION
    @apiPermission ARTICLE_PRIVACY
    @apiPermission ARTICLE_READ
    @apiPermission ARTICLE_CANCEL
    @apiPermission ARTICLE_AUDIT
    @apiUse Header
    @apiParam {number} [page=0] 文章信息列表页码, 页码为0时返回所有数据
    @apiParam {number} [page_size=10] 文章信息列表页长
    @apiParam {string} [section_name] 文章所属板块
    @apiParam {string} [author_uuid] 文章作者
    @apiParam {number=0, 1, 2, 3, 4, 5} [status] 文章状态，Cancel=0, Active=1, Draft=2, Audit=3,
                                                 Failed=4, Recycled=5，状态可拼接，e.g. '134'
    @apiParam {string} [order_field] 文章信息列表排序字段
    @apiParam {string=desc, asc} [order="desc"] 文章信息列表排序方向
    @apiParam {string} [query] 搜索内容，若无搜索字段则全局搜索title, keywords, content, author, section
    @apiParam {string=uuid, title, keywords, content,
               author, section, status, DjangoFilterParams} [query_field] 搜索字段, 支持Django filter参数
    @apiSuccess {String} total 文章信息列表总数
    @apiSuccess {String} articles 文章信息列表
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "articles": [
                {
                    "status": 1,
                    "dislike_count": 0,
                    "edit_at": "2018-02-27T16:00:00Z",
                    "uuid": "11d9fc3a-051f-5271-b1e1-65c192b63105",
                    "title": "test-update2",
                    "overview": "",
                    "section": 18,
                    "author": {
                        "remark": null,
                        "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                        "create_at": "2017-12-20T11:19:17Z",
                        "nick": "admin",
                        "role": 1,
                        "groups": []
                    },
                    "create_at": "2018-02-23T02:25:47Z",
                    "privacy": 1,
                    "like_count": 0,
                    "read_level": 200,
                    "keywords": "keyword1,keyword2",
                    "last_editor": {
                        "remark": null,
                        "uuid": "4be0643f-1d98-573b-97cd-ca98a65347dd",
                        "create_at": "2017-12-20T06:00:07Z",
                        "nick": "test",
                        "role": 2,
                        "groups": []
                    },
                    "id": 1,
                    "read_permission": true
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
    params = {
        'page': int,
        'page_size': int,
        'section_name': str,
        'author_uuid': str,
        'status': str,
        'order_field': str,
        'order': str,
        'query': str,
        'query_field': str
    }
    try:
        params_dict = request_parser(data=request.GET, params=params)
        code, data = ArticleService(request).list(**params_dict)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def article_create(request):
    """
    @api {post} /content/articles/ article create
    @apiVersion 0.1.0
    @apiName article_create
    @apiGroup content
    @apiDescription 创建文章
    @apiPermission ARTICLE_CREATE
    @apiPermission ARTICLE_PRIVACY
    @apiPermission ARTICLE_READ
    @apiPermission ARTICLE_CANCEL
    @apiPermission ARTICLE_AUDIT
    @apiUse Header
    @apiParam {string} title 文章标题
    @apiParam {string} [keywords] 文章关键词，e.g.'keyword1,keyword2'
    @apiParam {string} [cover_uuid] 文章封面UUID
    @apiParam {string} [overview={content(:200)}] 文章概述
    @apiParam {string} [content] 文章内容
    @apiParam {string} [section_name] 文章所属板块
    @apiParam {number=0, 1, 2, 3, 4, 5} [status=1] 文章状态, Cancel=0, Active=1, Draft=2, Audit=3,
                                                   Failed=4, Recycled=5
    @apiParam {number=0, 1, 2} [privacy=1] 文章私有状态, Private=0, Public=1, Protected=2
    @apiParam {number} [read_level=100] 文章需求阅读等级
    @apiParam {bool=true, false} [file_storage=false] 使用文件存储方式
    @apiSuccess {string} data 创建文章信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "status": 1,
            "dislike_count": 0,
            "edit_at": "2018-02-28",
            "uuid": "11d9fc3a-051f-5271-b1e1-65c192b63105",
            "title": "test-update2",
            "overview": "",
            "section": 18,
            "author": {
                "remark": null,
                "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                "create_at": "2017-12-20T11:19:17Z",
                "nick": "admin",
                "role": 1,
                "groups": []
            },
            "create_at": "2018-02-23T02:25:47Z",
            "content_url": null,
            "content": "content...",
            "privacy": 1,
            "like_count": 0,
            "read_level": 200,
            "keywords": "keyword1,keyword2",
            "last_editor": {
                "remark": null,
                "uuid": "4be0643f-1d98-573b-97cd-ca98a65347dd",
                "create_at": "2017-12-20T06:00:07Z",
                "nick": "test",
                "role": 2,
                "groups": []
            },
            "id": 1
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 403 Forbidden
    {
        "data": "Section permission denied"
    }
    """
    params = {
        'title': str,
        'keywords': list,
        'cover_uuid': str,
        'overview': str,
        'content': str,
        'section_name': str,
        'status': int,
        'privacy': int,
        'read_level': int,
        'file_storage': bool
    }
    try:
        params_dict = request_parser(data=request.POST, params=params)
        code, data = ArticleService(request).create(**params_dict)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def article_update(request, article_uuid):
    """
    @api {put} /content/articles/{uuid}/ article update
    @apiVersion 0.1.0
    @apiName article_update
    @apiGroup content
    @apiDescription 编辑文章
    @apiPermission ARTICLE_UPDATE
    @apiPermission ARTICLE_PRIVACY
    @apiPermission ARTICLE_READ
    @apiPermission ARTICLE_CANCEL
    @apiPermission ARTICLE_AUDIT
    @apiPermission ARTICLE_LIKE
    @apiUse Header
    @apiParam {string} title 文章标题
    @apiParam {string} [keywords] 文章关键词，e.g.'keyword1,keyword2'
    @apiParam {string} [cover_uuid] 文章封面UUID
    @apiParam {string} [overview] 文章概述
    @apiParam {string} [content] 文章内容
    @apiParam {string} [section_name] 文章所属板块
    @apiParam {number=0, 1, 2, 3, 4, 5} [status=1] 文章状态, Cancel=0, Active=1, Draft=2, Audit=3,
                                                   Failed=4, Recycled=5
    @apiParam {number=0, 1, 2} [privacy=1] 文章私有状态, Private=0, Public=1, Protected=2
    @apiParam {number} [read_level=100] 文章需求阅读等级
    @apiParam {number=0, 1} [like_operate] 文章点赞 Like=1, Dislike=0
    @apiSuccess {string} data 编辑文章信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "status": 1,
            "dislike_count": 0,
            "edit_at": "2018-02-28",
            "uuid": "11d9fc3a-051f-5271-b1e1-65c192b63105",
            "title": "test-update2",
            "overview": "",
            "section": 18,
            "author": {
                "remark": null,
                "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                "create_at": "2017-12-20T11:19:17Z",
                "nick": "admin",
                "role": 1,
                "groups": []
            },
            "create_at": "2018-02-23T02:25:47Z",
            "content_url": null,
            "content": "content...",
            "privacy": 1,
            "like_count": 0,
            "read_level": 200,
            "keywords": "keyword1,keyword2",
            "last_editor": {
                "remark": null,
                "uuid": "4be0643f-1d98-573b-97cd-ca98a65347dd",
                "create_at": "2017-12-20T06:00:07Z",
                "nick": "test",
                "role": 2,
                "groups": []
            },
            "id": 1
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
        'title': str,
        'keywords': list,
        'cover_uuid': str,
        'overview': str,
        'content': str,
        'section_name': str,
        'status': int,
        'privacy': int,
        'read_level': int,
        'like_operate': int
    }
    try:
        body = QueryDict(request.body)
        params_dict = request_parser(data=body, params=params)
        code, data = ArticleService(request).update(article_uuid=article_uuid,
                                                    **params_dict)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def article_delete(request, article_uuid):
    """
    @api {delete} /content/articles/[uuid]/ article delete
    @apiVersion 0.1.0
    @apiName article_delete
    @apiGroup content
    @apiDescription 删除文章
    @apiPermission ARTICLE_DELETE
    @apiPermission ARTICLE_CANCEL
    @apiUse Header
    @apiParam {string} [id_list] 删除文章uuid列表，e.g.'11d9fc3a-051f-5271-b1e1-65c192b63105,',
                                 当使用URL参数uuid时该参数忽略
    @apiParam {bool=true, false} [force=false] 强制删除
    @apiSuccess {string} data 文章删除信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "status": "SUCCESS",
                "id": "11d9fc3a-051f-5271-b1e1-65c192b63105",
                "name": "title..."
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
        if article_uuid:
            id_list = [{'delete_id': article_uuid, 'force': force}]
        else:
            id_list = data.get('id_list')
            if not isinstance(id_list, (unicode, str)):
                raise ParamsError()
            id_list = [{'delete_id': delete_id, 'force': force} for delete_id in id_list.split(',') if delete_id]
        code, data = 400, map(lambda params: ArticleService(request).delete(**params), id_list)
        for result in data:
            if result['status'] == 'SUCCESS':
                code = 200
                break
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)
