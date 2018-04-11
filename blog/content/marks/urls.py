from django.conf.urls import url

from blog.content.marks.views import mark_operate


urlpatterns = [
    url(r'^$', mark_operate),
    url(r'^(?P<mark_uuid>[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12})/$', mark_operate),
]
