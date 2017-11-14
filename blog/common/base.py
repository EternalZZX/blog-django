import base64
import memcache
import random
import time

from Crypto.Hash import MD5
from blog.settings import MEMCACHED_HOSTS


class Dictable(object):
    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def dict(self):
        return dict(self)

    def __iter__(self):
        return self.__dict__.items()


class NoneObject(object):
    def __getattr__(self, key):
        return self

    def __or__(self, other):
        return other

    def __and__(self, other):
        return self


class Response(object):
    def __init__(self, code=200, data=None):
        if data is None:
            data = {}
        self.code = code
        self.data = data


class MemcachedClient(object):
    def __init__(self):
        self.client = memcache.Client(MEMCACHED_HOSTS, debug=0)

    def set(self, key, value):
        return self.client.set(key, value)

    def get(self, key):
        return self.client.get(key)

    def replace(self, key, value):
        return self.client.replace(key, value)

    def delete(self, key):
        return self.client.delete(key)


class Authorize(object):
    def gen_token(self, uuid):
        rand = MD5.new()
        rand.update(str(random.random()))
        md5 = rand.hexdigest()
        token = base64.b64encode('ETE' + md5 + base64.b64encode(uuid)).rstrip('=')
        self.save_token(uuid=uuid, md5=md5)
        return token

    @staticmethod
    def save_token(uuid, md5):
        time_stamp = str(time.time()).split('.')[0]
        value = md5 + '&' + time_stamp
        MemcachedClient().set(key=uuid, value=value)

    @staticmethod
    def get_uuid(token):
        if len(token) > 4:
            code = token
            num = 4 - (len(token) % 4)
            if num < 4:
                for i in range(num):
                    code += '='
            code = base64.b64decode(code)
            if len(code) > 35 and code[:3] == 'ETE':
                return base64.b64decode(code[35:])
        return None


class Service(object):
    def __init__(self, request):
        self.request = request
        self.data = request.GET or request.POST
        self.user = self.data.get('user')
        self.token = request.META.get('HTTP_AUTH_TOKEN')
        self.auth(self.token)

    def auth(self, token):
        try:
            pass
            # middle_code = token[9:][:-6]
            # code_end = MemcachedClient().get(middle_code)
            # if code_end[-6:] != token[-6:]:
            #     raise OpenStackAPIError(code=ResponseCode.MULTI_LOGIN, message=u"您的账号已在其他设备登录!")
            # try:
            #     raw_code = base64.b64decode(base64.b64decode(base64.b64decode(middle_code)))
            # except:
            #     raise OpenStackAPIError(code=ResponseCode.TOKEN_ERROR, message=u"您的登录信息已失效!")
            #
            # if '&' not in raw_code:
            #     raise OpenStackAPIError(code=ResponseCode.TOKEN_ERROR, message=u"您的登录信息已失效!")
            # username, password = raw_code.split('&', 1)[0], raw_code.split('&', 1)[1]
            # self.username = username
            # if not Users.objects.filter(username=username, password=base64.b64encode(password)):
            #     raise OpenStackAPIError(code=ResponseCode.TOKEN_ERROR, message=u"您的登录信息已失效!")
        except Exception as e:
            pass
            # msg = getattr(e, 'message', "您的登录信息已失效!")
            # rcode = getattr(e, 'code', ResponseCode.TOKEN_ERROR)
            # aise OpenStackAPIError(code=code, message=msg)

