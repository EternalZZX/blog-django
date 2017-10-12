from django.conf.urls import patterns, url

from blog.account import views

urlpatterns = patterns('',
    url(r'^create/$', views.user_create),
    url(r'^delete/$', views.user_delete),
)
