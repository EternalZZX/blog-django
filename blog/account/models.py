from django.db import models


class ServerSetting(models.Model):
    key = models.CharField(primary_key=True, max_length=200)
    value = models.CharField(max_length=200)

    class Meta:
        db_table = 'server_setting'
