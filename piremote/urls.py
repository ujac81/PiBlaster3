from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^pages/(?P<page>[-\w]+)$', views.pages, name='pages'),
    url(r'^ajax/browse/$', views.browse_ajax, name='browse_ajax'),
    url(r'^ajax/status/$', views.status_ajax, name='status_ajax'),
    url(r'^ajax/cmd/$', views.cmd_ajax, name='cmd_ajax'),
    url(r'^ajax/plaction/$', views.plaction_ajax, name='plaction_ajax'),
    url(r'^ajax/plinfo/$', views.plinfo_ajax, name='plinfo_ajax'),
    url(r'^ajax/plinfo/(?P<pos>[\d]+)?$', views.plinfo_pos_ajax, name='plinfo_pos_ajax'),
    url(r'^ajax/plchanges/$', views.plchanges_ajax, name='plchanges_ajax'),
    url(r'^ajax/search/$', views.search_ajax, name='search_ajax'),
]

