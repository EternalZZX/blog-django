#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib

from django.http import HttpResponse, JsonResponse

from blog.wechat import receive, reply
from blog.common.message import ErrorMsg


def handle(request, uuid=None):
    if request.method == 'GET':
        return handle_get(request)
    elif request.method == 'POST':
        return handle_post(request)
    return JsonResponse({'data': ErrorMsg.REQUEST_METHOD_ERROR}, status=405)


def handle_get(request):
    try:
        if len(request.GET) == 0:
            return HttpResponse('')
        signature = request.GET.get('signature')
        timestamp = request.GET.get('timestamp')
        nonce = request.GET.get('nonce')
        echostr = request.GET.get('echostr')
        token = '66guitar'
        list = [token, timestamp, nonce]
        list.sort()
        sha1 = hashlib.sha1()
        map(sha1.update, list)
        hashcode = sha1.hexdigest()
        if hashcode == signature:
            return HttpResponse(echostr)
        else:
            return HttpResponse('')
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return JsonResponse({'data': data}, status=code)


def handle_post(request):
    try:
        receive_message = receive.parse_xml(request.body)
        if isinstance(receive_message, receive.Message) and receive_message.message_type == 'text':
            to_user = receive_message.from_username
            from_user = receive_message.to_username
            content = 'test'
            reply_message = reply.TextMessage(to_user, from_user, content)
            return reply_message.send()
        else:
            return HttpResponse('success')
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return JsonResponse({'data': data}, status=code)
