from django.db import models


class Group(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'group'
        ordering = ['id']
