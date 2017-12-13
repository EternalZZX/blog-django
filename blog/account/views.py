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
        if not uuid:
            response = user_list(request)
        else:
            response = user_get(request, uuid)
    elif request.method == 'POST':
        response = user_create(request)
    elif request.method == 'PUT':
        response = user_update(request, uuid)
    elif request.method == 'DELETE':
        response = user_delete(request, uuid)
    else:
        response = Response(code=405, data=ErrorMsg.REQUEST_METHOD_ERROR)
    return response


def user_get(request, uuid):
    """
    @api {get} /account/user/{uuid}/ user get
    @apiVersion 0.1.0
    @apiName user_get
    @apiGroup account
    @apiDescription 获取用户信息详情
    @apiPermission USER_SELECT
    @apiUse Header
    @apiSuccess {string} data 用户信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "remark": "C'est la vie",
            "gender": false,
            "create_at": "2017-12-06T09:15:49Z",
            "nick": "EternalZZX",
            "role": 1,
            "groups": 1
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 403 Forbidden
    {
        "data": "User not found"
    }
    """
    try:
        code, data = UserService(request).user_get(user_uuid=uuid)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def user_list(request):
    """
    @api {get} /account/user/ user list
    @apiVersion 0.1.0
    @apiName user_list
    @apiGroup account
    @apiDescription 获取用户信息列表
    @apiPermission USER_SELECT
    @apiUse Header
    @apiParam {number} [page=0] 用户信息列表页码, 页码为0时返回所有数据
    @apiParam {number} [page_size=10] 用户信息列表页长
    @apiParam {string} [order_field] 用户信息列表排序字段
    @apiParam {string=desc, asc} [order="desc"] 用户信息列表排序方向
    @apiParam {string} [query] 搜索内容，若无搜索字段则全局搜索nick, role, group, remark
    @apiParam {string=nick, role, group, remark, DjangoFilterParams} [query_field] 搜索字段, 支持Django filter参数
    @apiSuccess {String} total 用户信息列表总数
    @apiSuccess {String} users 用户信息列表
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "total": 1,
            "users": [
                {
                    "nick": "EternalZZX",
                    "remark": "C'est la vie",
                    "role": 1,
                    "create_at": "2017-12-06T09:15:49Z",
                    "groups": 1
                }
            ]
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 403 Forbidden
    {
        "data": "Order field permission denied"
    }
    """
    try:
        page = request.GET.get('page')
        page_size = request.GET.get('page_size')
        order_field = request.GET.get('order_field')
        order = request.GET.get('order')
        query = request.GET.get('query')
        query_field = request.GET.get('query_field')
        code, data = UserService(request).user_list(page=page,
                                                    page_size=page_size,
                                                    order_field=order_field,
                                                    order=order,
                                                    query=query,
                                                    query_field=query_field)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def user_create(request):
    """
    @api {post} /account/user/ user create
    @apiVersion 0.1.0
    @apiName user_create
    @apiGroup account
    @apiDescription 创建用户
    @apiPermission USER_CREATE
    @apiUse Header
    @apiParam {string} username 用户名
    @apiParam {string} password 密码
    @apiParam {string} [nick={username}] 昵称
    @apiParam {number} [role_id] 用户角色ID
    @apiParam {string} [group_ids] 用户组ID列表，e.g."2;9;32;43"
    @apiParam {number=0, 1} [gender] 性别, male=0, female=1
    @apiParam {string} [email] 电子邮箱地址
    @apiParam {string} [phone] 电话号码
    @apiParam {string} [qq] QQ号码
    @apiParam {string} [address] 收货地址
    @apiParam {string} [remark] 备注
    @apiSuccess {string} data 创建用户信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "username": "user",
            "qq": null,
            "remark": null,
            "uuid": "9e556479-7003-5916-9cd6-33f4227cec9b",
            "phone": null,
            "gender": null,
            "create_at": "2017-12-13T08:34:59.425Z",
            "email": null,
            "nick": "user",
            "role": 2,
            "groups": [],
            "address": null,
            "id": 29
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 400 Bad Request
    {
        "data": "Duplicate username"
    }
    """
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
