from django.conf.urls import url

from ..views import language


app_name = 'wagtail_page_translation'

urlpatterns = [
    url(r'^$', language.Index.as_view(), name='index'),
    url(r'^add/$', language.Create.as_view(), name='add'),
    url(r'^(\d+)/$', language.Edit.as_view(), name='edit'),
    url(r'^(\d+)/delete/$', language.Delete.as_view(), name='delete'),
]
