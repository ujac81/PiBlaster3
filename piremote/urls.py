from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^pages/(?P<page>[-\w]+)$', views.pages, name='pages'),
    url(r'^ajax/browse/$', views.browse_ajax, name='browse_ajax'),
    url(r'^ajax/status/$', views.status_ajax, name='status_ajax'),
    url(r'^ajax/cmd/$', views.cmd_ajax, name='cmd_ajax'),
    url(r'^ajax/plaction/$', views.plaction_ajax, name='plaction_ajax'),
    url(r'^ajax/plsaction/$', views.plsaction_ajax, name='plsaction_ajax'),
    url(r'^ajax/plinfo/$', views.plinfo_ajax, name='plinfo_ajax'),
    url(r'^ajax/plinfo/(?P<id>[\d]+)?/$', views.plinfo_id_ajax, name='plinfo_id_ajax'),
    url(r'^ajax/plshortinfo/$', views.plshortinfo_ajax, name='plshortinfo_ajax'),
    url(r'^ajax/plchanges/$', views.plchanges_ajax, name='plchanges_ajax'),
    url(r'^ajax/fileinfo/$', views.file_info_ajax, name='file_info_ajax'),
    url(r'^ajax/search/$', views.search_ajax, name='search_ajax'),
    url(r'^ajax/command/$', views.command_ajax, name='command_ajax'),
]

