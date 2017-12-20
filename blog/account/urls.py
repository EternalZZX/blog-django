from django.conf.urls import patterns, include, url


urlpatterns = patterns('blog.account.views',
                       url(r'^auth/$', 'auth'),
                       url(r'^users/', include('blog.account.users.urls')),
                       url(r'^roles/', include('blog.account.roles.urls')),
                       )
