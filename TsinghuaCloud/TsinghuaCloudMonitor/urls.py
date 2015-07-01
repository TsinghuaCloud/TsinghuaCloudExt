from django.conf.urls import patterns, url
from TsinghuaCloudMonitor import views

urlpatterns = patterns('',
    url(r'^register/$', views.register, name='register'),
    url(r'^monitor/hostdetail/$', views.hostdetail, name='hostdetail'),
    url(r'^tenants/$', views.gettenants,name='gettenants'),
    url(r'^subnets/$', views.getsubnets,name='getsubnets'), 
    url(r'^instances/$', views.getinstances,name='getinstances'), 
    url(r'^memory_external/$', views.memory_external,name='memory_external'),
    url(r'^cpu_external/$', views.cpu_external,name='cpu_external'),
    url(r'^pro_external/$', views.pro_external,name='pro_extern'),
    url(r'^disk_external/$', views.disk_external,name='disk_external'),
    url(r'^eth_external/$', views.eth_external,name='eth_external'),
    url(r'^hoststatus/$', views.hoststatus, name='hoststatus'),
    url(r'^hostdetail/([0-9]+)/$', views.hostdetail, name='hostdetail'),
    url(r'^request/([a-zA-Z0-9]+)/$', views.request, name='request'),
    url(r'^totalcompare/$', views.totalcompare, name='totalcompare'),
    url(r'^download_first/$', views.download_first, name='views.download_first'),
    url(r'^download_second/$', views.download_second, name='views.download_second'),
    url(r'^download_third/$', views.download_third, name='views.download_third'),
    url(r'^start_system/$', views.start_system, name='start_system'),
    url(r'^monitor/doSearch/$', views.doSearch, name='doSearch'),
    url(r'^schedule/scheduledata/$', views.schedule_data, name='scheduledata'),


)
