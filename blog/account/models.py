import uuid

from django.db import models
from django.dispatch import receiver


class User(models.Model):
    MALE = 0
    FEMALE = 1
    GENDER_CHOICES = (
        (MALE, 'male'),
        (FEMALE, 'female')
    )

    id = models.AutoField(primary_key=True)
    uuid = models.CharField(max_length=36,
                            default=str(uuid.uuid4()),
                            unique=True,
                            editable=False)
    username = models.SlugField()
    password = models.CharField(max_length=50)
    nick = models.CharField(max_length=200)
    role = models.ForeignKey('Role', null=True)
    groups = models.ManyToManyField('Group')
    gender = models.NullBooleanField(choices=GENDER_CHOICES, null=True)
    email = models.EmailField(null=True)
    phone = models.CharField(max_length=50, null=True)
    qq = models.CharField(max_length=50, null=True)
    address = models.CharField(max_length=1000, null=True)
    remark = models.TextField(null=True)
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user'


class UserPrivacySetting(models.Model):
    PUBLIC = 2
    PROTECTED = 1
    PRIVATE = 0
    PRIVACY_CHOICES = (
        (PUBLIC, 'public'),
        (PROTECTED, 'protected'),
        (PRIVATE, 'private')
    )

    user = models.OneToOneField('User', primary_key=True)
    gender_privacy = models.IntegerField(choices=PRIVACY_CHOICES, default=PUBLIC)
    email_privacy = models.IntegerField(choices=PRIVACY_CHOICES, default=PRIVATE)
    phone_privacy = models.IntegerField(choices=PRIVACY_CHOICES, default=PRIVATE)
    qq_privacy = models.IntegerField(choices=PRIVACY_CHOICES, default=PRIVATE)
    address_privacy = models.IntegerField(choices=PRIVACY_CHOICES, default=PRIVATE)

    class Meta:
        db_table = 'user_privacy_setting'


class UserSign(models.Model):
    user = models.OneToOneField('User', primary_key=True)
    sign_up_at = models.DateTimeField(auto_now_add=True)
    sign_in_last = models.DateTimeField(null=True)
    sign_in_err = models.IntegerField(default=0)

    class Meta:
        db_table = 'user_sign'


@receiver(models.signals.post_save, sender=User, dispatch_uid='models.user_obj_create')
def user_obj_create(sender, instance, created, **kwargs):
    if created:
        UserPrivacySetting.objects.create(user=instance)
        UserSign.objects.create(user=instance)


class Role(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    nick = models.CharField(max_length=200, null=True)
    role_level = models.IntegerField(default=0)
    default = models.BooleanField(default=False)
    permissions = models.ManyToManyField('Permission', through='RolePermission')
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'role'


class Permission(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    nick = models.CharField(max_length=200, null=True)

    class Meta:
        db_table = 'permission'


class RolePermission(models.Model):
    role = models.ForeignKey('Role')
    permission = models.ForeignKey('Permission')
    state = models.NullBooleanField(null=True)
    major_level = models.IntegerField(null=True)
    minor_level = models.IntegerField(null=True)
    value = models.IntegerField(null=True)

    class Meta:
        db_table = 'role_permission'


class Group(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'group'


class ServerSetting(models.Model):
    key = models.CharField(primary_key=True, max_length=200)
    value = models.CharField(max_length=200)

    class Meta:
        db_table = 'server_setting'
