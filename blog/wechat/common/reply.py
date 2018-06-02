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
