#!/usr/bin/env python
# -*- coding: utf-8 -*-

from blog.content.albums.services import AlbumService
from blog.wechat.common import reply
from blog.wechat.common.media import MediaService
from blog.common.base import Authorize
from blog.settings import TOKEN_URL_KEY


class ReceiveKeywords(object):
    TEST_TEXT = 'test-text'
    TEST_UPLOAD = 'test-upload'


class WeChatService(object):
    KEYWORDS = [
        ReceiveKeywords.TEST_TEXT,
        ReceiveKeywords.TEST_UPLOAD
    ]

    def __init__(self, receive_message):
        self.receive_message = receive_message
        self.to_user = self.receive_message.from_username
        self.from_user = self.receive_message.to_username

    def reply_keyword(self, keyword):
        if keyword == ReceiveKeywords.TEST_TEXT:
            return self.reply_text('test reply')
        elif keyword == ReceiveKeywords.TEST_UPLOAD:
            url = '/media/photos/7357d28a-a611-5efd-ae6e-a550a5b95487/middle/21012079-f263-5592-95cc-41459892161b.png'
            return self.reply_image(MediaService().photo_upload(url))

    def search_album(self, query):
        token = Authorize().gen_guest_token()['token']
        code, data = AlbumService(token=token).list(page=1,
                                                    page_size=8,
                                                    author_uuid='7357d28a-a611-5efd-ae6e-a550a5b95487',
                                                    query=query,
                                                    query_field='name')
        if code == 200:
            albums = data['albums']
            article_data = []
            for album in albums:
                article_data.append({
                    'title': album['name'],
                    'url': 'api.eternalzzx.com/view/albums/%s/?%s=%s' % (album['uuid'], TOKEN_URL_KEY, token)
                })
            if article_data:
                article_data[0]['photo_url'] = 'https://mmbiz.qpic.cn/mmbiz_jpg/NYuibG5m9i' \
                                               'bxicibg1NGYBXO8P5mglthfylgzdLX734NgqYP6eQi' \
                                               'cqf6fNFaXrWz9oibVw5d2k7unfm3z4rzr9ua9BFg/0?wx_fmt=jpeg'
                return self.reply_news(article_data)
        return self.reply_text('没有找到相关曲谱')

    def reply_text(self, content):
        return reply.TextMessage(self.to_user, self.from_user, content).send()

    def reply_image(self, media_id):
        return reply.ImageMessage(self.to_user, self.from_user, media_id).send()

    def reply_news(self, article_data):
        return reply.NewsMessage(self.to_user, self.from_user, len(article_data), article_data).send()
