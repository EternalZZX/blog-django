#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import QueryDict
from django.views.decorators.http import require_GET

from blog.account.users.services import UserService
from blog.common.base import Authorize
from blog.common.error import ParamsError
from blog.common.message import ErrorMsg
from blog.common.utils import Response, json_response, str_to_list


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


@json_response
@require_GET
def user_self(request):
    """
    @api {get} /account/users/self/ user self
    @apiVersion 0.1.0
    @apiName user_self
    @apiGroup account
    @apiDescription 获取用户自身信息详情
    @apiUse Header
    @apiSuccess {string} data 用户信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "remark": null,
            "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
            "create_at": "2017-12-20T11:19:17Z",
            "nick": "test",
            "role": 2,
            "avatar": "/media/photos/7357d28a-a611-5efd-ae6e-a550a5b95487.jpeg",
            "groups": []
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 403 Forbidden
    {
        "data": "Permission denied"
    }
    """
    request_token = request.META.get('HTTP_AUTH_TOKEN')
    try:
        uuid, user_id, role_id = Authorize().auth_token(request_token)
        code, data = 200, UserService.get_user_dict(user_id=user_id)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def user_get(request, uuid):
    """
    @api {get} /account/users/{uuid}/ user get
    @apiVersion 0.1.0
    @apiName user_get
    @apiGroup account
    @apiDescription 获取用户信息详情
    @apiPermission USER_SELECT
    @apiPermission USER_PRIVACY
    @apiPermission USER_CANCEL
    @apiUse Header
    @apiSuccess {string} data 用户信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "remark": null,
            "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
            "create_at": "2017-12-20T11:19:17Z",
            "nick": "admin",
            "role": 1,
            "avatar": "/media/photos/9b19df9b-25f5-5a09-a4ce-b7e0149699dc.jpeg",
            "groups": null
        }
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 404 Not Found
    {
        "data": "User not found"
    }
    """
    try:
        code, data = UserService(request).get(user_uuid=uuid)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def user_list(request):
    """
    @api {get} /account/users/ user list
    @apiVersion 0.1.0
    @apiName user_list
    @apiGroup account
    @apiDescription 获取用户信息列表
    @apiPermission USER_SELECT
    @apiPermission USER_PRIVACY
    @apiPermission USER_CANCEL
    @apiUse Header
    @apiParam {number} [page=0] 用户信息列表页码, 页码为0时返回所有数据
    @apiParam {number} [page_size=10] 用户信息列表页长
    @apiParam {string} [order_field] 用户信息列表排序字段
    @apiParam {string=desc, asc} [order="desc"] 用户信息列表排序方向
    @apiParam {string} [query] 搜索内容，若无搜索字段则全局搜索nick, role, group, remark
    @apiParam {string=uuid, nick, role, group, remark, DjangoFilterParams} [query_field] 搜索字段, 支持Django filter参数
    @apiSuccess {String} total 用户信息列表总数
    @apiSuccess {String} users 用户信息列表
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "total": 1,
            "users": [
                {
                    "remark": null,
                    "uuid": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                    "create_at": "2017-12-20T11:19:17Z",
                    "nick": "admin",
                    "role": 1,
                    "avatar": "/media/photos/9b19df9b-25f5-5a09-a4ce-b7e0149699dc.jpeg",
                    "groups": null
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
    page = request.GET.get('page')
    page_size = request.GET.get('page_size')
    order_field = request.GET.get('order_field')
    order = request.GET.get('order')
    query = request.GET.get('query')
    query_field = request.GET.get('query_field')
    try:
        code, data = UserService(request).list(page=page,
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
    @api {post} /account/users/ user create
    @apiVersion 0.1.0
    @apiName user_create
    @apiGroup account
    @apiDescription 创建用户
    @apiPermission USER_CREATE
    @apiPermission USER_STATUS
    @apiPermission USER_ROLE
    @apiUse Header
    @apiParam {string} username 用户名
    @apiParam {string} password 密码
    @apiParam {string} [nick={username}] 昵称
    @apiParam {number} [role_id] 用户角色ID
    @apiParam {string} [group_ids] 用户组ID列表，e.g.'2,9,32,43'
    @apiParam {number=0, 1} [gender] 性别, Female=0, Male=1
    @apiParam {string} [email] 电子邮箱地址
    @apiParam {string} [phone] 电话号码
    @apiParam {string} [qq] QQ号码
    @apiParam {string} [address] 收货地址
    @apiParam {number=0, 1} [status=1] 账号状态, Cancel=0, Active=1
    @apiParam {string} [remark] 备注
    @apiParam {number=0, 1, 2} [kwargs] 隐私设置, Private=0, Public=1, Protected=2
                                        参数名'gender_privacy', 'email_privacy',
                                        'phone_privacy', 'qq_privacy', 'address_privacy'
    @apiSuccess {string} data 创建用户信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "username": "test",
            "qq": null,
            "remark": null,
            "uuid": "4be0643f-1d98-573b-97cd-ca98a65347dd",
            "phone": null,
            "gender": true,
            "status": 1,
            "create_at": "2017-12-20T06:00:07Z",
            "email": null,
            "nick": "test",
            "role": 2,
            "avatar": null,
            "groups": [],
            "address": null,
            "id": 5,
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
    HTTP/1.1 409 Bad Request
    {
        "data": "Duplicate identity field"
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
    status = request.POST.get('status')
    remark = request.POST.get('remark')
    kwargs = {}
    for key in UserService.USER_PRIVACY_FIELD:
        value = request.POST.get(key)
        if value is not None:
            kwargs[key] = value
    try:
        group_ids = str_to_list(group_ids)
        code, data = UserService(request).create(username=username,
                                                 password=password,
                                                 nick=nick,
                                                 role_id=role_id,
                                                 group_ids=group_ids,
                                                 gender=gender,
                                                 email=email, phone=phone,
                                                 qq=qq, address=address,
                                                 status=status,
                                                 remark=remark, **kwargs)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def user_update(request, uuid):
    """
    @api {put} /account/users/{uuid}/ user update
    @apiVersion 0.1.0
    @apiName user_update
    @apiGroup account
    @apiDescription 编辑用户
    @apiPermission USER_UPDATE
    @apiPermission USER_STATUS
    @apiPermission USER_ROLE
    @apiUse Header
    @apiParam {string} [username] 用户名
    @apiParam {string} [old_password] 旧密码
    @apiParam {string} [new_password] 新密码
    @apiParam {string} [nick] 昵称
    @apiParam {string} [avatar_uuid] 用户头像UUID
    @apiParam {number} [role_id] 用户角色ID
    @apiParam {string} [group_ids] 用户组ID列表，e.g.'2,9,32,43'
    @apiParam {number=0, 1} [gender] 性别, Female=0, Male=1
    @apiParam {string} [email] 电子邮箱地址
    @apiParam {string} [phone] 电话号码
    @apiParam {string} [qq] QQ号码
    @apiParam {string} [address] 收货地址
    @apiParam {string} [remark] 备注
    @apiParam {number=0, 1, 2} [kwargs] 隐私设置, Private=0, Public=1, Protected=2
                                        参数名'gender_privacy', 'email_privacy',
                                        'phone_privacy', 'qq_privacy', 'address_privacy'
    @apiSuccess {string} data 编辑用户信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": {
            "username": "test",
            "qq": null,
            "remark": null,
            "uuid": "4be0643f-1d98-573b-97cd-ca98a65347dd",
            "phone": null,
            "gender": true,
            "status": 1,
            "create_at": "2017-12-20T06:00:07Z",
            "email": null,
            "nick": "test",
            "role": 2,
            "avatar": null,
            "groups": [],
            "address": null,
            "id": 5,
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
    HTTP/1.1 404 Not Found
    {
        "data": "User not found"
    }
    """
    data = QueryDict(request.body)
    username = data.get('username')
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    nick = data.get('nick')
    avatar_uuid = data.get('avatar_uuid')
    role_id = data.get('role_id')
    group_ids = data.get('group_ids')
    gender = data.get('gender')
    email = data.get('email')
    phone = data.get('phone')
    qq = data.get('qq')
    address = data.get('address')
    status = data.get('status')
    remark = data.get('remark')
    kwargs = {}
    for key in UserService.USER_PRIVACY_FIELD:
        value = data.get(key)
        if value is not None:
            kwargs[key] = value
    try:
        if group_ids is not None:
            group_ids = str_to_list(group_ids)
        code, data = UserService(request).update(user_uuid=uuid,
                                                 username=username,
                                                 old_password=old_password,
                                                 new_password=new_password,
                                                 nick=nick,
                                                 avatar_uuid=avatar_uuid,
                                                 role_id=role_id,
                                                 group_ids=group_ids,
                                                 gender=gender,
                                                 email=email, phone=phone,
                                                 qq=qq, address=address,
                                                 status=status, remark=remark,
                                                 **kwargs)
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)


def user_delete(request, uuid):
    """
    @api {delete} /account/users/[uuid]/ user delete
    @apiVersion 0.1.0
    @apiName user_delete
    @apiGroup account
    @apiDescription 删除用户
    @apiPermission USER_DELETE
    @apiPermission USER_CANCEL
    @apiUse Header
    @apiParam {string} [id_list] 删除用户uuid列表，e.g.'7357d28a-a611-5efd-ae6e-a550a5b95487,
                                 3cd43d89-ab0b-54ac-811c-1f4bb9b3fab6', 当使用URL参数uuid时
                                 该参数忽略
    @apiParam {bool=true, false} [force=false] 强制删除
    @apiSuccess {string} data 用户删除信息详情
    @apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "data": [
            {
                "status": "SUCCESS",
                "id": "7357d28a-a611-5efd-ae6e-a550a5b95487",
                "name": "test"
            }
        ]
    }
    @apiUse ErrorData
    @apiErrorExample {json} Error-Response:
    HTTP/1.1 403 Forbidden
    {
        "data": "Permission denied"
    }
    """
    data = QueryDict(request.body)
    force = data.get('force') == 'true'
    try:
        if uuid:
            id_list = [{'delete_id': uuid, 'force': force}]
        else:
            id_list = data.get('id_list')
            if not isinstance(id_list, (unicode, str)):
                raise ParamsError()
            id_list = [{'delete_id': delete_id, 'force': force} for delete_id in id_list.split(',') if delete_id]
        code, data = 400, map(lambda params: UserService(request).delete(**params), id_list)
        for result in data:
            if result['status'] == 'SUCCESS':
                code = 200
                break
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return Response(code=code, data=data)
