from django.db import models

from blog.account.users.models import User


class Mark(models.Model):
    PRIVATE = 0
    PUBLIC = 1
    PRIVACY_CHOICES = (
        (PRIVATE, 'private'),
        (PUBLIC, 'public')
    )

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True)
    author = models.ForeignKey(to=User, related_name='marks_create')
    color = models.CharField(max_length=10, null=True)
    attach_count = models.IntegerField(default=0)
    privacy = models.IntegerField(choices=PRIVACY_CHOICES, default=PUBLIC)
    create_at = models.DateTimeField(auto_now_add=True)

    def attach_mark(self, count=1):
        self.attach_count = self.attach_count + count
        self.save()

    def detach_mark(self, count=1):
        self.attach_count = self.attach_count - count
        self.save()

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


def get_resource_marks(res_id, res_type):
    marks = []
    resources = MarkResource.objects.filter(res_id=res_id, res_type=res_type)
    for resource in resources:
        mark = Mark.objects.get(id=resource.mark_id)
        marks.append(mark)
    return marks
