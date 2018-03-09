from django.conf.urls import patterns, url


urlpatterns = patterns('blog.content.photos.views',
                       url(r'^$', 'photo_operate'),
                       url(r'^(?P<photo_uuid>[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12})/$', 'photo_operate'),
                       )
