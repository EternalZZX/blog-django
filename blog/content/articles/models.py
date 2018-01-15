import uuid

from datetime import datetime
from django.db import models

from blog.account.users.models import User


class Article(models.Model):
    CANCEL = 0
    DRAFT = 1
    REVIEW = 2
    ACTIVE = 3
    STATUS_CHOICES = (
        (CANCEL, 'cancel'),
        (DRAFT, 'draft'),
        (REVIEW, 'review'),
        (ACTIVE, 'active')
    )

    PRIVATE = 0
    PROTECTED = 1
    PUBLIC = 2
    PRIVACY_CHOICES = (
        (PUBLIC, 'public'),
        (PROTECTED, 'protected'),
        (PRIVATE, 'private')
    )

    id = models.AutoField(primary_key=True)
    uuid = models.CharField(max_length=36,
                            default=str(uuid.uuid4()),
                            unique=True,
                            editable=False)
    title = models.CharField(max_length=200)
    keyword = models.TextField(null=True)
    content = models.TextField(null=True)
    author = models.ForeignKey(to=User, related_name='author')
    actors = models.ManyToManyField(to=User, related_name='actor')
    status = models.IntegerField(choices=STATUS_CHOICES, default=ACTIVE)
    privacy = models.IntegerField(choices=PRIVACY_CHOICES, default=PUBLIC)
    read_level = models.IntegerField(default=100)
    like_count = models.IntegerField(default=0)
    dislike_count = models.IntegerField(default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    last_editor = models.ForeignKey(to=User, related_name='last_editor')
    edit_at = models.DateTimeField(default=datetime.now())

    class Meta:
        db_table = 'article'
