from django.db import models

from blog.common.tools import BaseModel
from blog.account.groups.models import Group
from blog.account.roles.models import Role
from blog.account.users.models import User


class Section(models.Model, BaseModel):
    CANCEL = 0
    NORMAL = 1
    HIDE = 2
    STATUS_CHOICES = (
        (CANCEL, 'cancel'),
        (NORMAL, 'normal'),
        (HIDE, 'hide'),
    )

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    nick = models.CharField(max_length=200)
    description = models.TextField(null=True)
    moderators = models.ManyToManyField(to=User, related_name='moderator')
    assistants = models.ManyToManyField(to=User, related_name='assistant')
    status = models.IntegerField(choices=STATUS_CHOICES, default=NORMAL)
    read_level = models.IntegerField(default=0)
    only_roles = models.BooleanField(default=False)
    roles = models.ManyToManyField(to=Role, related_name='role')
    only_groups = models.BooleanField(default=False)
    groups = models.ManyToManyField(to=Group, related_name='group')
    creator = models.ForeignKey(User)
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'section'
