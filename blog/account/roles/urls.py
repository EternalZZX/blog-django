from django.conf.urls import patterns, url


urlpatterns = patterns('blog.account.roles.views',
                       url(r'^$', 'role_operate'),
                       url(r'^(?P<role_id>(\d+))/$', 'role_operate'),
                       )