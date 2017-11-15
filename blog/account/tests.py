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

# url = 'http://0.0.0.0:8000/blog/account/auth/'
# params = {
#     'username': 'admin',
#     'password': 'admin'
# }

url = 'http://0.0.0.0:8000/blog/account/user_create/'
params = {
    'username': 'test-user',
    'password': 'password'
}

response = requests.post(url, params)

print "code:", response.status_code
print 'body:', response.content
