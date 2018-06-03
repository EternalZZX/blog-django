#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib

from django.http import HttpResponse, JsonResponse

from blog.wechat.common import receive, reply
from blog.wechat.common.media import MediaService
from blog.wechat.services import WeChatService
from blog.common.message import ErrorMsg
from blog.settings import APP_TOKEN


def handle(request):
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
        stamp_list = [APP_TOKEN, timestamp, nonce]
        stamp_list.sort()
        sha1 = hashlib.sha1()
        map(sha1.update, stamp_list)
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
        if isinstance(receive_message, (receive.TextMessage, receive.ImageMessage)):
            if receive_message.message_type == 'text':
                if receive_message.content in WeChatService.KEYWORDS:
                    return WeChatService(receive_message).reply_keyword(receive_message.content)
                else:
                    return WeChatService(receive_message).search_album(receive_message.content)
            elif receive_message.message_type == 'image':
                return WeChatService(receive_message).reply_image(receive_message.media_id)
        return reply.Message().send()
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return JsonResponse({'data': data}, status=code)
