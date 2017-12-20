import uuid

from django.db import models
from django.dispatch import receiver

from blog.account.roles.models import Role
from blog.account.groups.models import Group


class User(models.Model):
    MALE = 0
    FEMALE = 1
    GENDER_CHOICES = (
        (MALE, 'male'),
        (FEMALE, 'female')
    )

    CANCEL = 0
    ACTIVE = 1
    STATUS_CHOICES = (
        (CANCEL, 'cancel'),
        (ACTIVE, 'female')
    )

    id = models.AutoField(primary_key=True)
    uuid = models.CharField(max_length=36,
                            default=str(uuid.uuid4()),
                            unique=True,
                            editable=False)
    username = models.SlugField()
    password = models.CharField(max_length=50)
    nick = models.CharField(max_length=200)
    role = models.ForeignKey(Role, null=True)
    groups = models.ManyToManyField(Group)
    gender = models.NullBooleanField(choices=GENDER_CHOICES, null=True)
    email = models.EmailField(unique=True, null=True)
    phone = models.CharField(unique=True, max_length=50, null=True)
    qq = models.CharField(max_length=50, null=True)
    address = models.CharField(max_length=1000, null=True)
    remark = models.TextField(null=True)
    status = models.IntegerField(choices=STATUS_CHOICES, default=ACTIVE)
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user'

    def update_char_field(self, key, value):
        if value is not None:
            if value == '':
                setattr(self, key, None)
            else:
                setattr(self, key, value)


class UserPrivacySetting(models.Model):
    PRIVATE = 0
    PROTECTED = 1
    PUBLIC = 2
    PRIVACY_CHOICES = (
        (PUBLIC, 'public'),
        (PROTECTED, 'protected'),
        (PRIVATE, 'private')
    )

    user = models.OneToOneField(User, primary_key=True)
    gender_privacy = models.IntegerField(choices=PRIVACY_CHOICES, default=PUBLIC)
    email_privacy = models.IntegerField(choices=PRIVACY_CHOICES, default=PRIVATE)
    phone_privacy = models.IntegerField(choices=PRIVACY_CHOICES, default=PRIVATE)
    qq_privacy = models.IntegerField(choices=PRIVACY_CHOICES, default=PRIVATE)
    address_privacy = models.IntegerField(choices=PRIVACY_CHOICES, default=PRIVATE)

    class Meta:
        db_table = 'user_privacy_setting'


class UserSign(models.Model):
    user = models.OneToOneField(User, primary_key=True)
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
