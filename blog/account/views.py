#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.views.decorators.http import require_POST

from blog.account.users.models import User
from blog.account.users.services import UserService
from blog.common.base import Authorize
from blog.common.error import AuthError, ParamsError
from blog.common.message import ErrorMsg, AccountErrorMsg
from blog.common.utils import Response, json_response, encode
from blog.common.setting import Setting, AuthType


@json_response
@require_POST
def sign_in(request):
    """
    @api {post} /account/sign_in/ sign in
    @apiVersion 0.1.0
    @apiName sign_in
    @apiGroup account
    @apiDescription 用户登录
    @apiPermission Guest
    @apiUse Header
    @apiParam {string} username 用户名
    @apiParam {string} password 密码
    @apiSuccess {string} data 用户身份验证信息
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "remark": null,
            "uuid": "3e673fdc-1a4f-5b16-8890-dbe7e763f7b5",
            "create_at": "2018-04-12T02:46:29Z",
            "nick": "test4",
            "token": "VpHTXRNV0UwWmkwMVlqRTJMVGc0T1RBdFpHSmxOMlUzTmpObU4ySTE",
            "role": 2,
            "avatar": null,
            "groups": []
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 403 Forbidden
    {
        "data": "Username and password do not match"
    }
    """
    username = request.POST.get('username')
    password = request.POST.get('password')
    if username and password:
        try:
            user = User.objects.get(username=username)
            if user.status == User.CANCEL or encode(password, user.uuid) != user.password:
                raise AuthError()
            code, data = 200, UserService.user_to_dict(user=user,
                                                       token=Authorize().gen_token(uuid=user.uuid))
        except (User.DoesNotExist, AuthError):
            code, data = 403, AccountErrorMsg.PASSWORD_ERROR
    else:
        code, data = 400, ErrorMsg.REQUEST_ERROR
    return Response(code=code, data=data)


@json_response
@require_POST
def sign_in_guest(request):
    """
    @api {post} /account/sign_in_guest/ guest sign in
    @apiVersion 0.1.0
    @apiName sign_in_guest
    @apiGroup account
    @apiDescription 访客登陆
    @apiPermission Guest
    @apiUse Header
    @apiSuccess {string} data 访客登陆信息
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "token": "RVRFZGYyZmU2MjhlYTg1NTk4OTFiODUzZDQyZTBiOGQ0YjlZbVF6WW",
            "role": 3,
            "uuid": "bd3b8c0b-3527-589e-8eb4-e59864dc90c3"
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 403 Forbidden
    {
        "data": "Guest permission denied"
    }
    """
    if Setting().GUEST:
        try:
            code, data = 200, Authorize().gen_guest_token()
        except Exception as e:
            code, data = getattr(e, 'code', 400), \
                         getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    else:
        code, data = 403, AccountErrorMsg.GUEST_ERROR
    return Response(code=code, data=data)


@json_response
@require_POST
def sign_up(request):
    """
    @api {post} /account/sign_up/ sign up
    @apiVersion 0.1.0
    @apiName sign_up
    @apiGroup account
    @apiDescription 用户注册
    @apiPermission Guest
    @apiUse Header
    @apiParam {string} username 用户名
    @apiParam {string} password 密码
    @apiSuccess {string} data 用户注册信息
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "username": "test",
            "qq": null,
            "remark": null,
            "uuid": "6bfe0b7d-bfe5-54e1-b446-f7056367f842",
            "phone": null,
            "gender": null,
            "status": 1,
            "create_at": "2018-04-12T03:01:40.322Z",
            "email": null,
            "nick": "test11",
            "token": "VpsTlMwMU5HVXhMV0kwTkRZdFpqY3dOVFl6TmpkbU9EUXk",
            "role": 2,
            "avatar": null,
            "groups": [],
            "address": null,
            "id": 15,
            "privacy_setting": {
                "email_privacy": 0,
                "phone_privacy": 0,
                "qq_privacy": 0,
                "gender_privacy": 1,
                "address_privacy": 0
            }
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 403 Forbidden
    {
        "data": "Sign up permission denied"
    }
    """
    # Todo sign up key
    if Setting().SIGN_UP:
        username = request.POST.get('username')
        password = request.POST.get('password')
        request_token = request.META.get('HTTP_AUTH_TOKEN')
        try:
            if not username or not password:
                raise ParamsError()
            code, data = UserService(request, auth_type=AuthType.NONE).create(username=username,
                                                                              password=password)
            if code is 201:
                code, data['token'] = 200, Authorize().gen_token(uuid=data['uuid'])
                if request_token:
                    Authorize().cancel_token(token=request_token)
        except Exception as e:
            code, data = getattr(e, 'code', 400), \
                         getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    else:
        code, data = 403, AccountErrorMsg.SIGN_UP_ERROR
    return Response(code=code, data=data)
