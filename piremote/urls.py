"""urls.py -- routes for piremote application.

Routes beginning with ajax/ should be accessed via AJAX only.
Response will be JSON for all ajax methods.
"""

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^upload/$', views.upload, name='upload'),
    url(r'^upload/ratings/$', views.upload_ratings, name='upload_ratings'),
    url(r'^upload/history/$', views.upload_history, name='upload_history'),
    url(r'^upload/smartpl/$', views.upload_smartpl, name='upload_smartpl'),
    url(r'^pages/(?P<page>[-\w]+)$', views.pages, name='pages'),
    url(r'^ajax/list/(?P<what>[\d\w\-\_]+)/$', views.list_ajax, name='list_ajax'),
    url(r'^ajax/browse/$', views.browse_ajax, name='browse_ajax'),
    url(r'^ajax/status/$', views.status_ajax, name='status_ajax'),
    url(r'^ajax/cmd/$', views.cmd_ajax, name='cmd_ajax'),
    url(r'^ajax/mixer/$', views.mixer_ajax, name='mixer_ajax'),
    url(r'^ajax/mixerset/$', views.mixerset_ajax, name='mixerset_ajax'),
    url(r'^ajax/plaction/$', views.plaction_ajax, name='plaction_ajax'),
    url(r'^ajax/plsaction/$', views.plsaction_ajax, name='plsaction_ajax'),
    url(r'^ajax/plinfo/$', views.plinfo_ajax, name='plinfo_ajax'),
    url(r'^ajax/plinfo/(?P<id>[\d]+)?/$', views.plinfo_id_ajax, name='plinfo_id_ajax'),
    url(r'^ajax/plshortinfo/$', views.plshortinfo_ajax, name='plshortinfo_ajax'),
    url(r'^ajax/plchanges/$', views.plchanges_ajax, name='plchanges_ajax'),
    url(r'^ajax/fileinfo/$', views.file_info_ajax, name='file_info_ajax'),
    url(r'^ajax/search/$', views.search_ajax, name='search_ajax'),
    url(r'^ajax/command/$', views.command_ajax, name='command_ajax'),
    url(r'^ajax/settings/$', views.settings_ajax, name='settings_ajax'),
    url(r'^ajax/set/$', views.set_ajax, name='set_ajax'),
    url(r'^ajax/upload/$', views.upload_ajax, name='upload_ajax'),
    url(r'^ajax/doupload/$', views.doupload_ajax, name='doupload_ajax'),
    url(r'^ajax/stats/$', views.stats_ajax, name='stats_ajax'),
    url(r'^ajax/listby/$', views.listby_ajax, name='listby_ajax'),
    url(r'^ajax/seedbrowse/$', views.seed_browse_ajax, name='seed_browse_ajax'),
    url(r'^ajax/history/$', views.history_ajax, name='history_ajax'),
    url(r'^ajax/rate/$', views.rate_ajax, name='rate_ajax'),
    url(r'^ajax/smartpl/(?P<action>[\d\w]+)/$', views.smartpl_ajax, name='smartpl_ajax'),
    url(r'^ajax/smartplaction/(?P<id>\d+)/(?P<action>\w+)/$', views.smartplaction_ajax, name='smartplaction_ajax'),
    url(r'^download/ratings/$', views.download_ratings, name='download_ratings'),
    url(r'^download/ratings/(?P<mode>[-\w]+)/$', views.download_ratings, name='download_ratings'),
    url(r'^download/history/$', views.download_history, name='download_history'),
    url(r'^ajax/download/smartpl/(?P<idx>\d+)/$', views.download_smartpl, name='download_smartpl'),
    url(r'^ajax/download/playlist/$', views.download_playlist, name='download_playlist'),
]

