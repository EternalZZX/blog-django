from django.conf.urls import patterns, url

from blog.account import views

urlpatterns = patterns('',
    url(r'^auth/$', views.auth),
    url(r'^user_create/$', views.user_create),
    url(r'^user_delete/$', views.user_delete),
)
