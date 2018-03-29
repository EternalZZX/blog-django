from django.conf.urls import url

from blog.content.sections.views import section_operate


urlpatterns = [
    url(r'^$', section_operate),
    url(r'^(?P<section_id>(\d+))/$', section_operate),
]
