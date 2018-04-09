from django.conf.urls import url

from blog.content.marks.views import mark_operate


urlpatterns = [
    url(r'^$', mark_operate),
    url(r'^(?P<mark_id>(\d+))/$', mark_operate),
]
