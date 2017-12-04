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
url = 'http://0.0.0.0:8000/blog/account/user_create/'

headers = {
    'Auth-Token': 'RVRFMGEwNGI1YjIzYWFjOTc4ODQ3N2Q1NDlmYTRlYjU2Y2VZbUZqWlRBM01ERXRNVFZsTXkwMU1UUTBMVGszWXpVdE5EYzBPRGRrTlRRek1ETXk'
}

# params = {
#     'username': 'admin',
#     'password': 'admin'
# }
params = {
    'username': 'test-user',
    'password': 'password'
}


response = requests.post(url, params, headers=headers)

print "code:", response.status_code
print 'body:', response.content
