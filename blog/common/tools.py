#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BaseModel(object):
    def __init__(self):
        pass

    def update_char_field(self, key, value):
        if value is not None:
            if value == '':
                setattr(self, key, None)
            else:
                setattr(self, key, value)

    @staticmethod
    def update_m2m_field(m2m_field, model, ids, id_field='id'):
        if ids is not None:
            m2m_field.clear()
            for id in ids:
                query_dict = {id_field: id}
                try:
                    m2m_field.add(model.objects.get(**query_dict))
                except model.DoesNotExist:
                    pass


def photo_large_path(instance, filename):
    return path_format(instance, filename, 'photos', size='large')


def photo_middle_path(instance, filename):
    return path_format(instance, filename, 'photos', size='middle')


def photo_small_path(instance, filename):
    return path_format(instance, filename, 'photos', size='small')


def photo_untreated_path(instance, filename):
    return path_format(instance, filename, 'photos', size='untreated')


def path_format(instance, filename, prefix, size=None):
    try:
        postfix = '.' + filename.split('.')[-1].lower()
    except (IndexError, AttributeError):
        postfix = ''
    if prefix == 'photos':
        return '%s/%s/%s/%s%s' % (prefix, instance.author.uuid, size, instance.uuid, postfix)
    elif prefix == 'articles':
        return '%s/%s/%s%s' % (prefix, instance.author.uuid, instance.uuid, postfix)
