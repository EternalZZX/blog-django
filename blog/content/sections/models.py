from django.db import models
from django.dispatch import receiver

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
    owner = models.ForeignKey(User)
    moderators = models.ManyToManyField(to=User, related_name='moderator')
    assistants = models.ManyToManyField(to=User, related_name='assistant')
    status = models.IntegerField(choices=STATUS_CHOICES, default=NORMAL)
    read_level = models.IntegerField(default=0)
    only_roles = models.BooleanField(default=False)
    roles = models.ManyToManyField(to=Role, related_name='role')
    only_groups = models.BooleanField(default=False)
    groups = models.ManyToManyField(to=Group, related_name='group')
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'section'


class SectionPolicy(models.Model):
    section = models.OneToOneField(Section, primary_key=True)
    auto_audit = models.BooleanField(default=False)
    article_mute = models.BooleanField(default=False)
    reply_mute = models.BooleanField(default=False)
    max_articles = models.IntegerField(null=True)
    max_articles_one_day = models.IntegerField(null=True)

    class Meta:
        db_table = 'section_policy'


class SectionPermission(models.Model):
    OWNER = 0
    MODERATOR = 1
    MANAGER = 2
    PERMISSION_CHOICES = (
        (OWNER, 'owner'),
        (MODERATOR, 'owner and moderator'),
        (MANAGER, 'owner, moderator and assistant')
    )

    section = models.OneToOneField(Section, primary_key=True)
    set_permission = models.IntegerField(choices=PERMISSION_CHOICES, default=OWNER)
    delete_permission = models.IntegerField(choices=PERMISSION_CHOICES, default=OWNER)
    set_owner = models.IntegerField(choices=PERMISSION_CHOICES, default=OWNER)
    set_name = models.IntegerField(choices=PERMISSION_CHOICES, default=OWNER)
    set_nick = models.IntegerField(choices=PERMISSION_CHOICES, default=MODERATOR)
    set_description = models.IntegerField(choices=PERMISSION_CHOICES, default=MANAGER)
    set_moderator = models.IntegerField(choices=PERMISSION_CHOICES, default=MODERATOR)
    set_assistant = models.IntegerField(choices=PERMISSION_CHOICES, default=MODERATOR)
    set_status = models.IntegerField(choices=PERMISSION_CHOICES, default=MODERATOR)
    set_cancel = models.IntegerField(choices=PERMISSION_CHOICES, default=MODERATOR)
    cancel_visible = models.IntegerField(choices=PERMISSION_CHOICES, default=MANAGER)
    set_read_level = models.IntegerField(choices=PERMISSION_CHOICES, default=MODERATOR)
    set_read_user = models.IntegerField(choices=PERMISSION_CHOICES, default=MODERATOR)
    set_policy = models.IntegerField(choices=PERMISSION_CHOICES, default=MODERATOR)
    article_audit = models.IntegerField(choices=PERMISSION_CHOICES, default=MANAGER)
    article_edit = models.IntegerField(choices=PERMISSION_CHOICES, default=MODERATOR)
    article_draft = models.IntegerField(choices=PERMISSION_CHOICES, default=MODERATOR)
    article_recycled = models.IntegerField(choices=PERMISSION_CHOICES, default=MODERATOR)
    article_cancel = models.IntegerField(choices=PERMISSION_CHOICES, default=MANAGER)
    article_delete = models.IntegerField(choices=PERMISSION_CHOICES, default=MODERATOR)

    class Meta:
        db_table = 'section_permission'


@receiver(models.signals.post_save, sender=Section, dispatch_uid='models.section_obj_create')
def section_obj_create(sender, instance, created, **kwargs):
    if created:
        SectionPolicy.objects.create(section=instance)
        SectionPermission.objects.create(section=instance)
