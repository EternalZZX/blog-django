from django.conf.urls import patterns, url

from blog.account import views

urlpatterns = patterns('',
    url(r'^auth/$', views.auth),
    url(r'^users/$', views.user_operate),
    url(r'^users/(?P<uuid>[a-f0-9]{8}-([a-f0-9]{4}-){3}[a-f0-9]{12})/$', views.user_operate),
)
