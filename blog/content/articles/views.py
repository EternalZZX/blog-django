#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import QueryDict

from blog.content.articles.services import ArticleService
from blog.common.message import ErrorMsg
from blog.common.error import ParamsError
from blog.common.utils import Response, json_response, str_to_list


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
    @api {get} /content/articles/{id}/ article get
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
    @apiUse Header
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
            "keywords": "keyword1;keyword2;",
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
    try:
        code, data = ArticleService(request).get(article_uuid=article_uuid)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def article_list(request):
    pass


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
    @apiParam {string} [keywords] 文章关键词，e.g.'keyword1;keyword2'
    @apiParam {string} [content] 文章内容
    @apiParam {string} [section_id] 文章所属板块ID
    @apiParam {number=0, 1, 2, 3, 4, 5} [status=1] 文章状态, Cancel=0, Active=1, Draft=2, Audit=3, Failed=4, Recycled=5
    @apiParam {number=0, 1, 2} [privacy=1] 文章私有状态, Private=0, Public=1, Protected=2
    @apiParam {number} [read_level=100] 文章需求阅读等级
    @apiSuccess {string} data 创建文章信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "status": 1,
            "dislike_count": 0,
            "edit_at": "2018-02-23T10:14:56.189",
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
            "create_at": "2018-02-23T02:25:47.382Z",
            "content_url": null,
            "content": "content...",
            "privacy": 1,
            "like_count": 0,
            "keywords": "keyword1;keyword2",
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
    title = request.POST.get('title')
    keywords = request.POST.get('keywords')
    content = request.POST.get('content')
    section_id = request.POST.get('section_id')
    status = request.POST.get('status')
    privacy = request.POST.get('privacy')
    read_level = request.POST.get('read_level')
    try:
        keywords = str_to_list(keywords)
        code, data = ArticleService(request).create(title=title,
                                                    keywords=keywords,
                                                    content=content,
                                                    section_id=section_id,
                                                    status=status,
                                                    privacy=privacy,
                                                    read_level=read_level)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def article_update(request, article_uuid):
    pass


def article_delete(request, article_uuid):
    pass