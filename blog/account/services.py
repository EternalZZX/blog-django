#!/usr/bin/env python
# -*- coding: utf-8 -*-

from Crypto.Hash import MD5

from blog.account.models import User
from blog.common.utils import model_to_dict
from blog.common.base import Service
from blog.common.error import ServiceError
from blog.common.message import ACCOUNT_ERROR_MSG


class UserService(Service):
    def user_create(self, username, password, nick=None, gender=None,
                    email=None, phone=None, qq=None, address=None, remark=None):
        if User.objects.filter(username=username):
            raise ServiceError(message=ACCOUNT_ERROR_MSG.DUPLICATE_USERNAME)
        md5 = MD5.new()
        md5.update(password)
        md5 = md5.hexdigest()
        user = User.objects.create(username=username, password=md5, nick=nick,
                                   gender=gender, email=email, phone=phone,
                                   qq=qq, address=address, remark=remark)
        return 200, model_to_dict(user)
