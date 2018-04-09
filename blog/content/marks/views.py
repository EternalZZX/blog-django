#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import QueryDict

from blog.content.marks.services import MetadataService
from blog.common.message import ErrorMsg
from blog.common.error import ParamsError
from blog.common.utils import Response, json_response, str_to_list


@json_response
def mark_operate(request, mark_id=None):
    if request.method == 'GET':
        if not mark_id:
            response = mark_list(request)
        else:
            response = mark_get(request, mark_id)
    elif request.method == 'POST':
        response = mark_create(request)
    elif request.method == 'PUT':
        response = mark_update(request, mark_id)
    elif request.method == 'DELETE':
        response = mark_delete(request, mark_id)
    else:
        response = Response(code=405, data=ErrorMsg.REQUEST_METHOD_ERROR)
    return response


def mark_get(request, mark_id):
    pass


def mark_list(request):
    pass


def mark_create(request):
    pass


def mark_update(request, mark_id):
    pass


def mark_delete(request, mark_id):
    pass
