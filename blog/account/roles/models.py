from django.db import models


class Role(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    nick = models.CharField(max_length=200)
    role_level = models.IntegerField(default=0)
    default = models.BooleanField(default=False)
    permissions = models.ManyToManyField(to='Permission', through='RolePermission')
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'role'
        ordering = ['id']


class Permission(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    nick = models.CharField(max_length=200)
    description = models.TextField(null=True)

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
