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