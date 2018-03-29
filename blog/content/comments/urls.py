from django.conf.urls import url

from blog.content.comments.views import comment_operate


urlpatterns = [
    url(r'^$', comment_operate),
    url(r'^(?P<comment_uuid>[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12})/$', comment_operate),
]
