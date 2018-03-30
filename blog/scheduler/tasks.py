#!/usr/bin/env python
# -*- coding: utf-8 -*-

from celery.task import task, periodic_task
from celery.schedules import crontab


@task(name='sync_redis')
def sync_redis_task():
    print('run sync_redis_task')


@periodic_task(name='sync_redis_periodic_task', run_every=(crontab(minute='*/1')))
def sync_redis_periodic_task():
    print('run sync_redis_periodic_task')
