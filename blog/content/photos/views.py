#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import QueryDict
from django.http import HttpResponse, JsonResponse

from blog.content.photos.services import PhotoService
from blog.common.message import ErrorMsg
from blog.common.error import ParamsError
from blog.common.utils import Response, json_response, str_to_list
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
    try:
        code, data = PhotoService(request).get(photo_uuid=photo_uuid)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def photo_list(request):
    pass


def photo_create(request):
    image = request.FILES.get('image')
    description = request.POST.get('description')
    album_uuid = request.POST.get('album_uuid')
    status = request.POST.get('status')
    privacy = request.POST.get('privacy')
    read_level = request.POST.get('read_level')
    try:
        code, data = PhotoService(request).create(image=image,
                                                  description=description,
                                                  album_uuid=album_uuid,
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
