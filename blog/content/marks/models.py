from django.db import models

from blog.account.users.models import User


class Mark(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    user = models.ForeignKey(User)
    color = models.CharField(max_length=10, null=False)
    attached = models.IntegerField(default=0)
    create_at = models.DateTimeField(auto_now_add=True)

    def attach_mark(self, att_num=1):
        self.attached += att_num
        self.save()

    def detach_mark(self, det_num=1):
        self.attached -= det_num
        self.save()

    class Meta:
        db_table = 'mark'


class MarkResource(models.Model):
    id = models.AutoField(primary_key=True)
    mark = models.ForeignKey(Mark)
    res_id = models.CharField(max_length=50, null=False)
    res_type = models.CharField(max_length=30, null=False)

    class Meta:
        db_table = 'mark_resource'


def get_resource_marks(res_id, res_type):
    marks = []
    resources = MarkResource.objects.filter(res_id=res_id, res_type=res_type)
    for resource in resources:
        mark = Mark.objects.get(id=resource.mark_id)
        marks.append(mark)
    return marks