from django.conf.urls import url

from blog.content.albums.views import album_operate


urlpatterns = [
    url(r'^$', album_operate),
    url(r'^(?P<album_uuid>[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12})/$', album_operate),
]
