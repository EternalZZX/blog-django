from django.conf.urls import patterns, url


urlpatterns = patterns('blog.content.sections.views',
                       url(r'^$', 'section_operate'),
                       url(r'^(?P<section_id>(\d+))/$', 'section_operate'),
                       )
