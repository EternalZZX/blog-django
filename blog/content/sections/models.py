from django.db import models

from blog.account.groups.models import Group
from blog.account.roles.models import Role
from blog.account.users.models import User


class Section(models.Model):
    CANCEL = 0
    VISIBLE_ONLY = 1
    ACTIVE = 2
    STATUS_CHOICES = (
        (CANCEL, 'cancel'),
        (VISIBLE_ONLY, 'visible_only'),
        (ACTIVE, 'active')
    )

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    nick = models.CharField(max_length=200)
    description = models.TextField(null=True)
    moderators = models.ManyToManyField(to=User, related_name='moderator')
    assistants = models.ManyToManyField(to=User, related_name='assistant')
    status = models.IntegerField(choices=STATUS_CHOICES, default=ACTIVE)
    level = models.IntegerField(default=0)
    only_roles = models.BooleanField(default=False)
    roles = models.ManyToManyField(to=Role, related_name='role')
    only_groups = models.BooleanField(default=False)
    groups = models.ManyToManyField(to=Group, related_name='group')

    class Meta:
        db_table = 'section'
