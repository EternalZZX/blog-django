#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

from django.http import HttpResponse


class Message(object):
    def send(self):
        return HttpResponse('success')


class TextMessage(Message):
    def __init__(self, to_username, from_username, content):
        self.__dict = dict()
        self.__dict['ToUserName'] = to_username
        self.__dict['FromUserName'] = from_username
        self.__dict['CreateTime'] = int(time.time())
        self.__dict['Content'] = content

    def send(self):
        xml_form = """
        <xml>
        <ToUserName><![CDATA[{ToUserName}]]></ToUserName>
        <FromUserName><![CDATA[{FromUserName}]]></FromUserName>
        <CreateTime>{CreateTime}</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[{Content}]]></Content>
        </xml>
        """
        return HttpResponse(xml_form.format(**self.__dict))


class ImageMessage(Message):
    def __init__(self, to_username, from_username, media_id):
        self.__dict = dict()
        self.__dict['ToUserName'] = to_username
        self.__dict['FromUserName'] = from_username
        self.__dict['CreateTime'] = int(time.time())
        self.__dict['MediaId'] = media_id

    def send(self):
        xml_form = """
        <xml>
        <ToUserName><![CDATA[{ToUserName}]]></ToUserName>
        <FromUserName><![CDATA[{FromUserName}]]></FromUserName>
        <CreateTime>{CreateTime}</CreateTime>
        <MsgType><![CDATA[image]]></MsgType>
        <Image>
        <MediaId><![CDATA[{MediaId}]]></MediaId>
        </Image>
        </xml>
        """
        return HttpResponse(xml_form.format(**self.__dict))


class NewsMessage(Message):
    def __init__(self, to_username, from_username, article_count, article_data):
        self.__dict = dict()
        self.__dict['ToUserName'] = to_username
        self.__dict['FromUserName'] = from_username
        self.__dict['CreateTime'] = int(time.time())
        self.__dict['ArticleCount'] = article_count
        self.__dict['ArticleData'] = self._format_article_data(article_data)

    @staticmethod
    def _format_article_data(article_data):
        xml_form = ""
        article_xml = """
        <item>
            <Title><![CDATA[{Title}]]></Title>
            <Description><![CDATA[{Description}]]></Description>
            <PicUrl><![CDATA[{PhotoUrl}]]></PicUrl>
            <Url><![CDATA[{Url}]]></Url>
        </item>
        """
        for article in article_data:
            params_dict = dict()
            params_dict['Title'] = article.title
            params_dict['Description'] = article.description
            params_dict['PhotoUrl'] = article.photo_url
            params_dict['Url'] = article.url
            xml_form = "%s%s" % (xml_form, article_xml.format(**params_dict))
        return xml_form

    def send(self):
        xml_form = """
        <xml>
        <ToUserName><![CDATA[{ToUserName}]]></ToUserName>
        <FromUserName><![CDATA[{FromUserName}]]></FromUserName>
        <CreateTime>{CreateTime}</CreateTime>
        <MsgType><![CDATA[news]]></MsgType>
        <ArticleCount>{ArticleCount}</ArticleCount>
        <Articles>{ArticleData}</Articles>
        </xml>
        """
        return HttpResponse(xml_form.format(**self.__dict))
