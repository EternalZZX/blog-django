#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ElementTree


def parse_xml(data):
    if len(data) == 0:
        return None
    xml_data = ElementTree.fromstring(data)
    message_type = xml_data.find('MsgType').text
    if message_type == 'text':
        return TextMessage(xml_data)
    elif message_type == 'image':
        return ImageMessage(xml_data)


class Message(object):
    def __init__(self, xml_data):
        self.to_username = xml_data.find('ToUserName').text
        self.from_username = xml_data.find('FromUserName').text
        self.create_at = xml_data.find('CreateTime').text
        self.message_type = xml_data.find('MsgType').text
        self.message_id = xml_data.find('MsgId').text


class TextMessage(Message):
    def __init__(self, xml_data):
        Message.__init__(self, xml_data)
        self.content = xml_data.find('Content').text.encode("utf-8")


class ImageMessage(Message):
    def __init__(self, xml_data):
        Message.__init__(self, xml_data)
        self.photo_url = xml_data.find('PicUrl').text
        self.media_id = xml_data.find('MediaId').text
