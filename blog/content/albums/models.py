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

    id = models.AutoField(primary_key=True)
    uuid = models.CharField(max_length=36,
                            default=str(uuid.uuid4()),
                            unique=True,
                            editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True)
    author = models.ForeignKey(to=User, related_name='album_author')
    privacy = models.IntegerField(choices=PRIVACY_CHOICES, default=PUBLIC)
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'album'
