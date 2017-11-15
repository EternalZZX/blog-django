#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.views.decorators.http import require_POST

from blog.account.services import UserService
from blog.common.base import Response
from blog.common.utils import json_response
from blog.common.message import ERROR_MSG


@json_response
@require_POST
def user_create(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    nick = request.POST.get('nick')
    gender = request.POST.get('gender')
    email = request.POST.get('email')
    phone = request.POST.get('phone')
    qq = request.POST.get('qq')
    address = request.POST.get('address')
    remark = request.POST.get('remark')
    try:
        code, data = UserService(request).user_create(username=username,
                                                      password=password,
                                                      nick=nick, gender=gender,
                                                      email=email, phone=phone,
                                                      qq=qq, address=address,
                                                      remark=remark)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ERROR_MSG.REQUEST_ERROR)
    return Response(code=code, data=data)


@json_response
@require_POST
def user_delete(request):
    return Response()
