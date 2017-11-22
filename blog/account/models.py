import uuid
from django.db import models


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
    nick = models.CharField(max_length=200, null=True)
    role = models.ForeignKey('Role')
    groups = models.ManyToManyField('Group')
    gender = models.NullBooleanField(choices=GENDER_CHOICES, null=True)
    email = models.EmailField(null=True)
    phone = models.CharField(max_length=50, null=True)
    qq = models.CharField(max_length=50, null=True)
    address = models.CharField(max_length=1000, null=True)
    remark = models.TextField(null=True)

    class Meta:
        db_table = 'user'


class UserSign(models.Model):
    user = models.ForeignKey('User', primary_key=True)
    sign_up_at = models.DateTimeField(auto_now_add=True)
    sign_in_last = models.DateTimeField(null=True)
    sign_in_err = models.IntegerField(default=0)

    class Meta:
        db_table = 'user_sign'


class Role(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    nick = models.CharField(max_length=200, null=True)
    login_perm = models.BooleanField(default=True)
    stealth_perm = models.BooleanField(default=True)
    search_perm = models.BooleanField(default=True)
    custom_title_perm = models.BooleanField(default=False)
    read_perm = models.IntegerField(default=1)
    report_perm = models.IntegerField(default=0)
    reply_perm = models.IntegerField(default=1)
    message_perm = models.IntegerField(default=1)
    operate_perm = models.IntegerField(default=0)

    class Meta:
        db_table = 'role'


class Group(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)

    class Meta:
        db_table = 'group'