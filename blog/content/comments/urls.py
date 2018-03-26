from django.conf.urls import patterns, url


urlpatterns = patterns('blog.content.comments.views',
                       url(r'^$', 'comment_operate'),
                       url(r'^(?P<comment_uuid>[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12})/$', 'comment_operate'),
                       )
