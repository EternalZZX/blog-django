from django.conf.urls import patterns, include, url


urlpatterns = patterns('',
                       url(r'^blog/v1/account/', include('blog.account.urls')),
                       url(r'^blog/v1/content/articles/', include('blog.content.articles.urls')),
                       url(r'^blog/v1/content/sections/', include('blog.content.sections.urls')),
                       )
