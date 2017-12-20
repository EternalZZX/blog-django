#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.views.decorators.http import require_POST

from blog.account.users.models import User
from blog.common.base import Authorize
from blog.common.error import AuthError
from blog.common.message import ErrorMsg, AccountErrorMsg
from blog.common.utils import Response, json_response, encode


@json_response
@require_POST
def auth(request):
    """
    @api {post} /account/auth/ token generate
    @apiVersion 0.1.0
    @apiName auth
    @apiGroup account
    @apiDescription 获取/更新用户身份验证Token
    @apiPermission Guest
    @apiUse Header
    @apiParam {string} [username] 用户名
    @apiParam {string} [password] 密码
    @apiSuccess {string} data 用户身份验证Token
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": "ZWVjM2ZaRE0xTlRNME56TXRZbUZsWXkwMU9EVmxMVGt4TlRVdE9EZ3laVGMxTWpSak1EZ3o"
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
    token = request.META.get('HTTP_AUTH_TOKEN')
    code, data = 400, ErrorMsg.REQUEST_ERROR
    if username and password:
        try:
            user = User.objects.get(username=username)
            if user.status == User.CANCEL \
                    or encode(password, user.uuid) != user.password:
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
