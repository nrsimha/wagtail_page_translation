from django.conf.urls import url

from ..views import translation


app_name = 'wagtail_page_translation'

urlpatterns = [
    url(r'^(\d+)/$', translation.revisions_index, name='index'),
    url(r'^(\d+)/add-translation/([-\w]+)/$', translation.add_translation,
        name='add_translation'),
]
