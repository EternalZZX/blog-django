import uuid

from django.db import models
from django.dispatch import receiver

from blog.common.tools import BaseModel
from blog.account.users.models import User


class Mark(models.Model, BaseModel):
    PRIVATE = 0
    PUBLIC = 1
    PRIVACY_CHOICES = (
        (PRIVATE, 'private'),
        (PUBLIC, 'public')
    )

    id = models.AutoField(primary_key=True)
    uuid = models.CharField(max_length=36,
                            default=str(uuid.uuid4()),
                            unique=True,
                            editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True)
    author = models.ForeignKey(to=User, related_name='marks_create')
    color = models.CharField(max_length=10, null=True)
    attach_count = models.IntegerField(default=0)
    privacy = models.IntegerField(choices=PRIVACY_CHOICES, default=PUBLIC)
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mark'


class MarkResource(models.Model):
    ARTICLE = 0
    ALBUM = 1
    PHOTO = 2
    TYPE_CHOICES = (
        (ARTICLE, 'article'),
        (ALBUM, 'album'),
        (PHOTO, 'photo')
    )

    id = models.AutoField(primary_key=True)
    mark = models.ForeignKey(to=Mark, related_name='resources')
    resource_type = models.IntegerField(choices=TYPE_CHOICES, default=ARTICLE)
    resource_uuid = models.CharField(max_length=36)

    class Meta:
        db_table = 'mark_resource'


@receiver(models.signals.post_save, sender=MarkResource,
          dispatch_uid='models.mark_resource_obj_create')
def mark_resource_obj_create(sender, instance, created, **kwargs):
    if created:
        attach_count = instance.mark.attach_count + 1
        instance.mark.attach_count = attach_count
        instance.mark.save()


@receiver(models.signals.pre_delete, sender=MarkResource,
          dispatch_uid='models.mark_resource_obj_delete')
def mark_resource_obj_delete(sender, instance, **kwargs):
    attach_count = instance.mark.attach_count - 1
    instance.mark.attach_count = attach_count
    instance.mark.save()
