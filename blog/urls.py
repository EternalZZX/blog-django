from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
                       url(r'^blog/v1/account/', include('blog.account.urls')),
                       )
