from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
                       url(r'^blog/v1/account/', include('blog.account.urls')),
                       url(r'^blog/v1/content/sections/', include('blog.content.sections.urls')),
                       )
