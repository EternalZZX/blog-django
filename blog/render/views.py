#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.views.decorators.http import require_GET

from blog.content.albums.services import AlbumService
from blog.content.photos.services import PhotoService
from blog.common.error import ServiceError
from blog.settings import TOKEN_URL_KEY


@require_GET
def album_show(request, uuid):
    token = request.GET.get(TOKEN_URL_KEY)
    try:
        album_service = AlbumService(token=token)
        code, album_data = album_service.get(album_uuid=uuid)
        if code == 200:
            code, photos_data = PhotoService(instance=album_service).list(album_uuid=uuid)
            return render(request, 'album.html', {
                'token': token,
                'album': album_data,
                'photos': photos_data['photos']
            })
    except ServiceError:
        return render(request, 'album.html')