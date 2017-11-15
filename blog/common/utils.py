#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import JsonResponse
from django.db.models.fields.related import ManyToManyField

from blog.common.base import Dictable, Response


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
        return JsonResponse(data, status=status_code)
    wrapper.__name__ = fun.__name__
    return wrapper


def model_to_dict(instance, **kwargs):
    if not instance:
        return instance
    opts = instance._meta
    data = {}
    for field in opts.concrete_fields + opts.many_to_many:
        if isinstance(field, ManyToManyField):
            if instance.pk is None:
                data[field.name] = []
            else:
                data[field.name] = list(field.value_from_object(instance).values_list('pk', flat=True))
        else:
            data[field.name] = field.value_from_object(instance)
    for key, value in kwargs.items():
        if key:
            data[key] = value
    return data
