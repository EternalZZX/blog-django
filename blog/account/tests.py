#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# from django.test import TestCase
# from django.test.client import Client
#
#
# class Test(TestCase):
#     def test_api(self):
#         url = '/blog/account/auth/'
#         params = {
#             'username': 'admin',
#             'password': 'admin'
#         }
#
#         self.client = Client()
#         response = self.client.post(url, params)
#         print response


import requests
import sys


reload(sys)
sys.setdefaultencoding('utf8')

url = 'http://0.0.0.0:8000/blog/account/auth/'
params = {
    'username': 'admin',
    'password': 'admin'
}

response = requests.post(url, params)

print '\n'.join(['%s:%s' % item for item in response.__dict__.items()])
print "code:", response.status_code
print 'data:', response.content