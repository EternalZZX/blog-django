#!/usr/bin/env python
# -*- coding: utf-8 -*-

from celery.task import task, periodic_task
from celery.schedules import crontab

from blog.content.albums.services import AlbumMetadataService
from blog.content.articles.services import ArticleMetadataService
from blog.content.comments.services import CommentMetadataService
from blog.content.photos.services import PhotoMetadataService
from blog.wechat.common.base import AccessService


@task(name='sync_redis')
def sync_redis_task():
    ArticleMetadataService().sync_metadata()
    CommentMetadataService().sync_metadata()
    PhotoMetadataService().sync_metadata()
    AlbumMetadataService().sync_metadata()


@task(name='wechat_access_token')
def update_access_token_task():
    AccessService.update_access_token()


# @periodic_task(name='sync_redis_periodic_task', run_every=(crontab(minute='*/1')))
# def sync_redis_periodic_task():
#     print('run sync_redis_periodic_task')
