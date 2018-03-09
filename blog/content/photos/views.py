#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import QueryDict

from blog.content.photos.services import PhotoService
from blog.common.message import ErrorMsg
from blog.common.error import ParamsError
from blog.common.utils import Response, json_response, str_to_list

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
    pass


def photo_list(request):
    pass


def photo_create(request):
    image = request.FILES.get('image')
    description = request.POST.get('description')
    status = request.POST.get('status')
    privacy = request.POST.get('privacy')
    read_level = request.POST.get('read_level')
    try:
        code, data = PhotoService(request).create(image=image,
                                                  description=description,
                                                  status=status,
                                                  privacy=privacy,
                                                  read_level=read_level)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def photo_update(request, photo_uuid):
    pass


def photo_delete(request, photo_uuid):
    pass
