from django.shortcuts import render
from django.views.decorators.http import require_POST

from blog.common.base import Response
from blog.common.utils import json_response


@json_response
@require_POST
def user_create(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    return Response()


@json_response
@require_POST
def user_delete(request):
    return Response()
