#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Crypto.Hash import MD5

from django.views.decorators.http import require_POST
from django.http import QueryDict

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
        try:
            user = User.objects.get(username=username)
            md5 = MD5.new()
            md5.update(user.uuid)
            md5.update(password + md5.hexdigest())
            md5 = md5.hexdigest()
            if md5 != user.password:
                raise AuthError()
            code, data = 200, Authorize().gen_token(uuid=user.uuid)
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
def user_operate(request, uuid=None):
    if request.method == 'GET':
        response = user_select(request, uuid)
    elif request.method == 'POST':
        response = user_create(request)
    elif request.method == 'PUT':
        response = user_update(request, uuid)
    elif request.method == 'DELETE':
        response = user_delete(request, uuid)
    else:
        response = Response(code=405, data=ErrorMsg.REQUEST_METHOD_ERROR)
    return response


def user_select(request, uuid):
    if not uuid:
        page = request.GET.get('page')
        page_size = request.GET.get('page_size')
        order_field = request.GET.get('order_field')
        order = request.GET.get('order')
        query = request.GET.get('query')
        query_field = request.GET.get('query_field')
        try:
            code, data = UserService(request).user_list(page=page,
                                                        page_size=page_size,
                                                        order_field=order_field,
                                                        order=order,
                                                        query=query,
                                                        query_field=query_field)
        except Exception as e:
            code, data = getattr(e, 'code', 400), \
                         getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    else:
        try:
            code, data = UserService(request).user_get(user_uuid=uuid)
        except Exception as e:
            code, data = getattr(e, 'code', 400), \
                         getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


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
    kwargs = {}
    for key in UserService.USER_PRIVACY_FIELD:
        kwargs[key] = request.POST.get(key)
    try:
        if isinstance(group_ids, (unicode, str)):
            group_ids = [group_id for group_id in group_ids.split(';') if group_id]
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
                                                      remark=remark, **kwargs)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def user_update(request, uuid):
    data = QueryDict(request.body)
    id = data.get('id')
    return Response()


def user_delete(request, uuid):
    data = QueryDict(request.body)
    id = data.get('id')
    return Response(code=200, data=uuid)
