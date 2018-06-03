#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib

from django.http import HttpResponse, JsonResponse

from blog.wechat.common import receive, reply
from blog.wechat.common.media import MediaService
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
            to_user = receive_message.from_username
            from_user = receive_message.to_username
            if receive_message.message_type == 'text':
                if receive_message.content == 'news':
                    article_data = [{
                        'title': 'title1',
                        'description': 'description1',
                        'photo_url': 'https://mmbiz.qpic.cn/mmbiz_jpg/NYuibG5m9ibxicibg1NGYBXO8P5mglthfylgzdLX734NgqYP6eQicqf6fNFaXrWz9oibVw5d2k7unfm3z4rzr9ua9BFg/0?wx_fmt=jpeg',
                        'url': 'www.eternalzzx.com'
                    }, {
                        'title': 'title2',
                        'description': 'description2',
                        'photo_url': 'https://mmbiz.qpic.cn/mmbiz_jpg/NYuibG5m9ibxicibg1NGYBXO8P5mglthfylgzdLX734NgqYP6eQicqf6fNFaXrWz9oibVw5d2k7unfm3z4rzr9ua9BFg/0?wx_fmt=jpeg',
                        'url': 'www.eternalzzx.com'
                    }, {
                        'title': 'title3',
                        'description': 'description3',
                        'photo_url': 'https://mmbiz.qpic.cn/mmbiz_jpg/NYuibG5m9ibxicibg1NGYBXO8P5mglthfylgzdLX734NgqYP6eQicqf6fNFaXrWz9oibVw5d2k7unfm3z4rzr9ua9BFg/0?wx_fmt=jpeg',
                        'url': 'www.eternalzzx.com'
                    }]
                    reply_message = reply.NewsMessage(to_user, from_user, 3, article_data)
                elif receive_message.content == 'image':
                    media_id = MediaService().photo_upload('/media/photos/7357d28a-a611-5efd-ae6e-a550a5b95487/'
                                                           'middle/21012079-f263-5592-95cc-41459892161b.png')
                    reply_message = reply.ImageMessage(to_user, from_user, media_id)
                else:
                    content = 'test'
                    reply_message = reply.TextMessage(to_user, from_user, content)
            elif receive_message.message_type == 'image':
                media_id = receive_message.media_id
                reply_message = reply.ImageMessage(to_user, from_user, media_id)
            else:
                reply_message = reply.Message()
            return reply_message.send()
        else:
            return reply.Message().send()
    except Exception as e:
        code, data = getattr(e, 'code', 400), \
                     getattr(e, 'message', ErrorMsg.REQUEST_ERROR)
    return JsonResponse({'data': data}, status=code)
