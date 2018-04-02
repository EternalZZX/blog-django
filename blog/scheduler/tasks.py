#!/usr/bin/env python
# -*- coding: utf-8 -*-

from celery.task import task, periodic_task
from celery.schedules import crontab

from blog.content.articles.services import ArticleMetadataService


@task(name='sync_redis')
def sync_redis_task():
    ArticleMetadataService().sync_metadata()


# @periodic_task(name='sync_redis_periodic_task', run_every=(crontab(minute='*/1')))
# def sync_redis_periodic_task():
#     print('run sync_redis_periodic_task')
