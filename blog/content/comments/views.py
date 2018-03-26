#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import QueryDict

from blog.content.articles.services import ArticleService
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
    pass


def comment_list(request):
    pass


def comment_create(request):
    pass


def comment_update(request, comment_uuid):
    pass


def comment_delete(request, comment_uuid):
    pass
