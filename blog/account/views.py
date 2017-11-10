from django.shortcuts import render

from blog.common.result import Response
from blog.common.utils import json_response


@json_response
def user_create(request):
    return Response()


@json_response
def user_delete(request):
    return Response()
