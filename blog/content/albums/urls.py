from django.conf.urls import patterns, url


urlpatterns = patterns('blog.content.albums.views',
                       url(r'^$', 'album_operate'),
                       url(r'^(?P<album_uuid>[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12})/$', 'album_operate'),
                       )