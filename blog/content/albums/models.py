import uuid

from django.db import models
from django.dispatch import receiver

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
    ALBUM_COVER_ALBUM = 1
    SECTION_COVER_ALBUM = 2
    ARTICLE_COVER_ALBUM = 3
    SYSTEM_ALBUM_CHOICES = (
        (AVATAR_ALBUM, 'avatar album'),
        (ALBUM_COVER_ALBUM, 'album cover album'),
        (SECTION_COVER_ALBUM, 'section cover album'),
        (ARTICLE_COVER_ALBUM, 'article cover album'),
    )

    id = models.AutoField(primary_key=True)
    uuid = models.CharField(max_length=36,
                            default=str(uuid.uuid4()),
                            unique=True,
                            editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True)
    cover = models.CharField(max_length=300, null=True)
    author = models.ForeignKey(to=User)
    privacy = models.IntegerField(choices=PRIVACY_CHOICES, default=PUBLIC)
    system = models.IntegerField(choices=SYSTEM_ALBUM_CHOICES, null=True)
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'album'


class AlbumMetaData(models.Model):
    album = models.OneToOneField(Album, primary_key=True,
                                 related_name='metadata', on_delete=models.CASCADE)
    read_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    dislike_count = models.IntegerField(default=0)
    like_users = models.ManyToManyField(to=User, related_name='albums_like')
    dislike_users = models.ManyToManyField(to=User, related_name='albums_dislike')

    class Meta:
        db_table = 'album_metadata'


@receiver(models.signals.post_save, sender=Album, dispatch_uid='models.album_obj_create')
def album_obj_create(sender, instance, created, **kwargs):
    if created:
        AlbumMetaData.objects.create(album=instance)
