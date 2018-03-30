import uuid

from django.utils import timezone
from django.db import models
from django.dispatch import receiver

from blog.common.tools import BaseModel
from blog.account.users.models import User
from blog.content.sections.models import Section


class Article(models.Model, BaseModel):
    CANCEL = 0
    ACTIVE = 1
    DRAFT = 2
    AUDIT = 3
    FAILED = 4
    RECYCLED = 5
    STATUS_CHOICES = (
        (CANCEL, 'cancel'),
        (ACTIVE, 'active'),
        (DRAFT, 'draft'),
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
    title = models.CharField(max_length=200)
    keywords = models.TextField(null=True)
    cover = models.CharField(max_length=300, null=True)
    overview = models.CharField(max_length=1000)
    content = models.TextField(null=True)
    content_url = models.CharField(null=True, max_length=1000)
    author = models.ForeignKey(to=User, related_name='articles_create')
    section = models.ForeignKey(Section, null=True, on_delete=models.SET_NULL)
    status = models.IntegerField(choices=STATUS_CHOICES, default=ACTIVE)
    privacy = models.IntegerField(choices=PRIVACY_CHOICES, default=PUBLIC)
    read_level = models.IntegerField(default=100)
    create_at = models.DateTimeField(auto_now_add=True)
    last_editor = models.ForeignKey(to=User, related_name='articles_edit')
    edit_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'article'


class ArticleMetaData(models.Model):
    article = models.OneToOneField(Article, primary_key=True,
                                   related_name='metadata', on_delete=models.CASCADE)
    read_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    dislike_count = models.IntegerField(default=0)
    like_users = models.ManyToManyField(to=User, related_name='articles_like')
    dislike_users = models.ManyToManyField(to=User, related_name='articles_dislike')

    class Meta:
        db_table = 'article_metadata'


@receiver(models.signals.post_save, sender=Article, dispatch_uid='models.article_obj_create')
def article_obj_create(sender, instance, created, **kwargs):
    if created:
        ArticleMetaData.objects.create(article=instance)
