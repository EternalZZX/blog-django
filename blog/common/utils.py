#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from Crypto.Hash import MD5
from contextlib import contextmanager

from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, InvalidPage, PageNotAnInteger
from django.db.models.fields.files import ImageField
from django.db.models.fields.related import ManyToManyField


class _Const(object):
    class ConstError(TypeError):
        pass

    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise self.ConstError("Cannot change const %s" % name)
        self.__dict__[name] = value


class StaticObject(object):
    def __init__(self):
        pass

    @classmethod
    def __iter__(cls):
        properties = filter(lambda item: item[0][:1] != '_', cls.__dict__.items())
        return iter(properties)


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


def json_response(fun):
    def wrapper(*args, **kwargs):
        result = fun(*args, **kwargs)
        if isinstance(result, Response):
            data, status_code = result.data, result.code
        elif isinstance(result, dict):
            data, status_code = result, 200
        elif isinstance(result, Dictable):
            data, status_code = result.dict(), 200
        else:
            data, status_code = {}, 500
        return JsonResponse({'data': data}, status=status_code)
    wrapper.__name__ = fun.__name__
    return wrapper


@contextmanager
def ignored(*exceptions):
    try:
        yield
    except exceptions:
        pass


def paging(object_list, page=0, page_size=10):
    total = len(object_list)
    if page <= 0:
        return object_list, total
    try:
        paginator = Paginator(object_list, page_size)
        if page > paginator.num_pages:
            page = paginator.num_pages
        page_list = paginator.page(page).object_list
    except (EmptyPage, InvalidPage, PageNotAnInteger):
        page_list = object_list
    return page_list, total


def model_to_dict(instance, **kwargs):
    if not hasattr(instance, '_meta'):
        return instance
    opts = instance._meta
    data = {}
    for field in opts.concrete_fields + opts.many_to_many:
        if isinstance(field, ManyToManyField):
            if instance.pk is None:
                data[field.name] = []
            else:
                data[field.name] = list(field.value_from_object(instance).values_list('pk', flat=True))
        elif isinstance(field, ImageField):
            try:
                url = field.value_from_object(instance).url
            except ValueError:
                url = None
            data[field.name] = url
        else:
            data[field.name] = field.value_from_object(instance)
    for key, value in kwargs.items():
        if key:
            data[key] = value
    return data


def str_to_list(data):
    if isinstance(data, (unicode, str)):
        return [item for item in data.split(';') if item]
    else:
        return []


def html_to_str(html):
    return re.compile(r'<[^>]+>', re.S).sub('', html)


def encode(data, salt):
    md5 = MD5.new()
    md5.update(salt)
    md5.update(data + md5.hexdigest())
    return md5.hexdigest()
