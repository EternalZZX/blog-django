from django.conf.urls import patterns, url


urlpatterns = patterns('blog.account.users.views',
    url(r'^$', 'user_operate'),
    url(r'^(?P<uuid>[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12})/$', 'user_operate'),
)
