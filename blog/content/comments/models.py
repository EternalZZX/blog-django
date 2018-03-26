import uuid

from django.utils import timezone
from django.db import models

from blog.common.tools import BaseModel
from blog.account.users.models import User


class Comment(models.Model, BaseModel):
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

    ARTICLE = 0
    COMMENT = 1
    ALBUM = 2
    PHOTO = 3
    TYPE_CHOICES = (
        (ARTICLE, 'article'),
        (COMMENT, 'comment'),
        (ALBUM, 'album'),
        (PHOTO, 'photo')
    )

    id = models.AutoField(primary_key=True)
    uuid = models.CharField(max_length=36,
                            default=str(uuid.uuid4()),
                            unique=True,
                            editable=False)
    resource_type = models.IntegerField(choices=TYPE_CHOICES, default=ARTICLE)
    resource_uuid = models.CharField(max_length=36)
    resource_author = models.ForeignKey(to=User, related_name='resource_author', null=True)
    content = models.TextField(null=True)
    author = models.ForeignKey(to=User, related_name='comment_author')
    status = models.IntegerField(choices=STATUS_CHOICES, default=ACTIVE)
    like_count = models.IntegerField(default=0)
    dislike_count = models.IntegerField(default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    last_editor = models.ForeignKey(to=User, related_name='comment_last_editor')
    edit_at = models.DateTimeField(default=timezone.now())

    class Meta:
        db_table = 'comment'
