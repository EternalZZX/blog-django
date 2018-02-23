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
    pass


def article_list(request):
    pass


def article_create(request):
    title = request.POST.get('title')
    keywords = request.POST.get('keywords')
    content = request.POST.get('content')
    content_url = request.POST.get('content_url')
    actor_uuids = request.POST.get('actor_uuids')
    section_id = request.POST.get('section_id')
    status = request.POST.get('status')
    privacy = request.POST.get('privacy')
    read_level = request.POST.get('read_level')
    try:
        keywords = str_to_list(keywords)
        actor_uuids = str_to_list(actor_uuids)
        code, data = ArticleService(request).create(title=title,
                                                    keywords=keywords,
                                                    content=content,
                                                    content_url=content_url,
                                                    actor_uuids=actor_uuids,
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