import uuid

from django.utils import timezone
from django.db import models
from django.dispatch import receiver

from blog.account.users.models import User
from blog.content.sections.models import Section


class Comment(models.Model):
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
    ALBUM = 1
    PHOTO = 2
    TYPE_CHOICES = (
        (ARTICLE, 'article'),
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
    resource_author = models.ForeignKey(to=User, related_name='resource_comment', null=True)
    resource_section = models.ForeignKey(to=Section, related_name='resource_section', null=True)
    dialog_uuid = models.CharField(max_length=73, null=True)
    reply_comment = models.ForeignKey(to='self', related_name='reply', null=True)
    content = models.TextField(null=True)
    author = models.ForeignKey(to=User, related_name='comments_create')
    status = models.IntegerField(choices=STATUS_CHOICES, default=ACTIVE)
    create_at = models.DateTimeField(auto_now_add=True)
    last_editor = models.ForeignKey(to=User, related_name='comments_edit')
    edit_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'comment'


class CommentMetaData(models.Model):
    comment = models.OneToOneField(Comment, primary_key=True,
                                   related_name='metadata', on_delete=models.CASCADE)
    read_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    dislike_count = models.IntegerField(default=0)
    like_users = models.ManyToManyField(to=User, related_name='comments_like')
    dislike_users = models.ManyToManyField(to=User, related_name='comments_dislike')

    class Meta:
        db_table = 'comment_metadata'


@receiver(models.signals.post_save, sender=Comment, dispatch_uid='models.comment_obj_create')
def comment_obj_create(sender, instance, created, **kwargs):
    if created:
        CommentMetaData.objects.create(comment=instance)
