import uuid

from django.utils import timezone
from django.db import models
from django.dispatch.dispatcher import receiver

from blog.account.users.models import User
from blog.content.albums.models import Album
from blog.common.tools import BaseModel
from blog.common.tools import photo_large_path, photo_middle_path, \
                              photo_small_path, photo_untreated_path


class Photo(models.Model, BaseModel):
    CANCEL = 0
    ACTIVE = 1
    AUDIT = 2
    FAILED = 3
    RECYCLED = 4
    STATUS_CHOICES = (
        (CANCEL, 'cancel'),
        (ACTIVE, 'active'),
        (AUDIT, 'audit'),
        (FAILED, 'failed'),
        (RECYCLED, 'recycled')
    )

    PRIVATE = 0
    PUBLIC = 1
    PROTECTED = 2
    PRIVACY_CHOICES = (
        (PRIVATE, 'private'),
        (PUBLIC, 'public'),
        (PROTECTED, 'protected')
    )

    id = models.AutoField(primary_key=True)
    uuid = models.CharField(max_length=36,
                            default=str(uuid.uuid4()),
                            unique=True,
                            editable=False)
    image_large = models.ImageField(upload_to=photo_large_path, null=True)
    image_middle = models.ImageField(upload_to=photo_middle_path, null=True)
    image_small = models.ImageField(upload_to=photo_small_path, null=True)
    image_untreated = models.ImageField(upload_to=photo_untreated_path, null=True)
    description = models.CharField(max_length=200)
    author = models.ForeignKey(to=User, related_name='photo_author')
    album = models.ForeignKey(Album, null=True, on_delete=models.SET_NULL)
    status = models.IntegerField(choices=STATUS_CHOICES, default=ACTIVE)
    privacy = models.IntegerField(choices=PRIVACY_CHOICES, default=PUBLIC)
    read_level = models.IntegerField(default=100)
    like_count = models.IntegerField(default=0)
    dislike_count = models.IntegerField(default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    last_editor = models.ForeignKey(to=User, related_name='photo_last_editor')
    edit_at = models.DateTimeField(default=timezone.now())

    class Meta:
        db_table = 'photo'


@receiver(models.signals.pre_delete, sender=Photo)
def photo_obj_delete(sender, instance, **kwargs):
    instance.image_large.delete(save=False)
    instance.image_middle.delete(save=False)
    instance.image_small.delete(save=False)
    instance.image_untreated.delete(save=False)
