#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Crypto.Hash import MD5

from django.views.decorators.http import require_POST

from blog.account.models import User
from blog.account.services import UserService
from blog.common.base import Authorize
from blog.common.utils import Response, json_response
from blog.common.error import AuthError
from blog.common.message import ErrorMsg, AccountErrorMsg


@json_response
@require_POST
def auth(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    token = request.META.get('HTTP_AUTH_TOKEN')
    code, data = 400, ErrorMsg.REQUEST_ERROR
    if username and password:
        md5 = MD5.new()
        md5.update(password)
        md5 = md5.hexdigest()
        try:
            uuid = User.objects.get(username=username, password=md5).uuid
            code, data = 200, Authorize().gen_token(uuid=uuid)
        except (User.DoesNotExist, AuthError):
            code, data = 403, AccountErrorMsg.PASSWORD_ERROR
    elif token:
        try:
            code, data = 200, Authorize().update_token(token=token)
        except AuthError as e:
            code, data = getattr(e, 'code', 400), \
                         getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


@json_response
@require_POST
def user_create(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    nick = request.POST.get('nick')
    role_id = request.POST.get('role_id')
    group_ids = request.POST.get('group_ids')
    gender = request.POST.get('gender')
    email = request.POST.get('email')
    phone = request.POST.get('phone')
    qq = request.POST.get('qq')
    address = request.POST.get('address')
    remark = request.POST.get('remark')
    try:
        if isinstance(group_ids, str):
            group_ids = [id for id in group_ids.split(';') if id]
        else:
            group_ids = []
        code, data = UserService(request).user_create(username=username,
                                                      password=password,
                                                      nick=nick,
                                                      role_id=role_id,
                                                      group_ids=group_ids,
                                                      gender=gender,
                                                      email=email, phone=phone,
                                                      qq=qq, address=address,
                                                      remark=remark)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


@json_response
@require_POST
def user_delete(request):
    return Response()
