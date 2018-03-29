from django.conf.urls import url

from blog.content.photos.views import photo_operate


urlpatterns = [
    url(r'^$', photo_operate),
    url(r'^(?P<photo_uuid>[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12})/$', photo_operate),
]
