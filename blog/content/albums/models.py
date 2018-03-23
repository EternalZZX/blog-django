import uuid

from django.db import models

from blog.common.tools import BaseModel
from blog.account.users.models import User


class Album(models.Model, BaseModel):
    PRIVATE = 0
    PUBLIC = 1
    PROTECTED = 2
    PRIVACY_CHOICES = (
        (PRIVATE, 'private'),
        (PUBLIC, 'public'),
        (PROTECTED, 'protected')
    )

    AVATAR_ALBUM = 0
    COVER_ALBUM = 1
    SYSTEM_ALBUM_CHOICES = (
        (AVATAR_ALBUM, 'avatar album'),
        (COVER_ALBUM, 'cover album')
    )

    id = models.AutoField(primary_key=True)
    uuid = models.CharField(max_length=36,
                            default=str(uuid.uuid4()),
                            unique=True,
                            editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True)
    cover = models.CharField(max_length=300, null=True)
    author = models.ForeignKey(to=User, related_name='album_author')
    privacy = models.IntegerField(choices=PRIVACY_CHOICES, default=PUBLIC)
    system = models.IntegerField(choices=SYSTEM_ALBUM_CHOICES, null=True)
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'album'
