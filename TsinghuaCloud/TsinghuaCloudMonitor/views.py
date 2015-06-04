import base64, urllib, httplib, json, os
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.shortcuts import render_to_response
from TsinghuaCloudMonitor.models import User
from TsinghuaCloudMonitor.models import Service
from TsinghuaCloudMonitor.models import HostStatus
from TsinghuaCloudMonitor.models import Host
from TsinghuaCloudMonitor.models import Schedule
from django.template.defaulttags import csrf_token
from django.db.models import Count, Max
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.http import StreamingHttpResponse
from django.contrib import auth
import re
import time
import subprocess as sub

import json
# Create your views here.

def homepage(request):
    return render(request, 'TsinghuaCloudMonitor/homepage.html')


def request(request, tenantid):
    # Redirect to login page if not logged in
    username = request.session['username']
    usergroup = request.session['usergroup']
    if username == None:
        return HttpResponseRedirect('/login')
    if username == '':
        return HttpResponseRedirect('/login')

    flag = 1
    return render(request, 'TsinghuaCloudMonitor/submap.html', {'flag': flag, 'tenantid': tenantid})


@csrf_exempt
def start_system(request):
    # Redirect to login page if not logged in
    username = request.session['username']
    usergroup = request.session['usergroup']
    if username == None:
        return HttpResponseRedirect('/login')
    if username == '':
        return HttpResponseRedirect('/login')

    return render(request, 'TsinghuaCloudMonitor/start_system.html')


def start_input(request):
    # Redirect to login page if not logged in
    username = request.session['username']
    usergroup = request.session['usergroup']
    if username == None:
        return HttpResponseRedirect('/login')
    if username == '':
        return HttpResponseRedirect('/login')

    return render(request, 'TsinghuaCloudMonitor/start_input.html')


def timestamp_datetime(value):
    format = '%Y-%m-%d %H:%M:%S'
    value = time.localtime(value)
    dt = time.strftime(format, value)
    return dt


def get_ports(headers):
    url = "166.111.143.220:9696"
    conn = httplib.HTTPConnection(url)
    conn.request("GET", "/v2.0/ports", "", headers)
    response = conn.getresponse()
    data = response.read()
    dd = json.loads(data)
    conn.close()
    return dd


def get_one_subnet_instances(subnetid, headers):
    res = []
    ports = get_ports(headers)
    for port in ports['ports']:
        if port['fixed_ips'][0]['subnet_id'] == subnetid and port['status'] == 'ACTIVE' and port[
            'device_owner'] == 'compute:None':
            res.append(port)
    return res


def get_subnets(headers):
    url = "166.111.143.220:9696"
    conn = httplib.HTTPConnection(url)
    # params = '{"tenant_id": "%s"} ' % projectid
    conn.request("GET", "/v2.0/subnets", "", headers)
    response = conn.getresponse()
    data = response.read()
    dd = json.loads(data)
    conn.close()
    return dd


def get_one_tenant_subnets(projectid, headers):
    res = []
    subnets = get_subnets(headers)
    for subnet in subnets['subnets']:
        if subnet['tenant_id'] == projectid:
            res.append(subnet)
    return res


def get_admin_token():
    url1 = "166.111.143.220:5000"
    params1 = '{"auth": {"tenantName": "admin","passwordCredentials": { "username": "admin","password": "cloud"}}}'
    headers1 = {"Content-Type": 'application/json'}
    conn1 = httplib.HTTPConnection(url1)
    conn1.request("POST", "/v2.0/tokens", params1, headers1)
    response1 = conn1.getresponse()
    data1 = response1.read()
    dd1 = json.loads(data1)
    conn1.close()
    token = dd1['access']['token']['id']
    return token


def get_tenants():
    url1 = "166.111.143.220:5000"
    token = get_admin_token()
    headers1 = {"X-Auth-Token": token, "Content-Type": 'application/json'}
    conn1 = httplib.HTTPConnection(url1)
    conn1.request("GET", "/v3/projects", "", headers1)
    response1 = conn1.getresponse()
    data1 = response1.read()
    dd1 = json.loads(data1)
    conn1.close()
    return dd1


@csrf_exempt
def gettenants(request):
    result = {}
    result = get_tenants()
    return HttpResponse(json.dumps(result), content_type="application/json")


@csrf_exempt
def getsubnets(request):
    result = {}
    token = get_admin_token()
    print "true:getsubnets"
    if request.GET.has_key('tenantid'):
        print "true: tenantid"
        tenantid = request.GET['tenantid']  # require the tenantid from js-ajax
        headers = {"X-Auth-Token": token, "Content-Type": 'application/json'}
        result = get_one_tenant_subnets(tenantid, headers)
        return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        print "not get getsubnets request!"


@csrf_exempt
def getinstances(request):
    result = {}
    print "getinstances!!!!!!"
    token = get_admin_token()
    if request.GET.has_key('subnetid'):
        subnetid = request.GET['subnetid']
        headers = {"X-Auth-Token": token, "Content-Type": 'application/json'}
        result = get_one_subnet_instances(subnetid, headers)
        return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        print "not get getinstances request!"


def monitor(request):
    # Redirect to login page if not logged in
    username = request.session['username']
    usergroup = request.session['usergroup']
    if username == None:
        return HttpResponseRedirect('/login')
    if username == '':
        return HttpResponseRedirect('/login')

    maxservice = Service.objects.all().values('HostName', 'ServiceName').order_by('HostName').annotate(
        max=Max('LastCheck')).filter(HostName__in=Host.objects.all().values('HostName'))
    service = []
    for k in range(0, len(maxservice)):
        current_host = get_object_or_404(Host, HostName=maxservice[k].get('HostName'))  # Max service host?
        # Only showing external host
        if current_host.HostType != 'external':
            continue
        # If user.group = user, show his own hosts. If user.group = admin, show all hosts.
        if usergroup == 'user' and current_host.Owner != username:
            continue
        temp = Service.objects.filter(HostName=maxservice[k].get('HostName'),
                                      ServiceName=maxservice[k].get('ServiceName'), LastCheck=maxservice[k].get('max'))
        for i in range(0, len(temp)):
            temp[i].HostType = 'external'
            service.append(temp[i])

    # print service
    return render(request, 'TsinghuaCloudMonitor/monitor.html', {'service': service, 'usergroup': usergroup})


def doSearch(request):
    # Redirect to login page if not logged in
    username = request.session['username']
    usergroup = request.session['usergroup']
    if username == None:
        return HttpResponseRedirect('/login')
    if username == '':
        return HttpResponseRedirect('/login')

    select_service = request.POST.get('service')
    select_host = request.POST.get('host')
    print select_service
    maxservice = Service.objects.all().values('ServiceName', 'HostName').annotate(max=Max('LastCheck'))
    service_1 = []
    for k in range(0, len(maxservice)):
        temp = Service.objects.filter(HostName=maxservice[k].get('HostName'),
                                      ServiceName=maxservice[k].get('ServiceName'), LastCheck=maxservice[k].get('max'))
        for i in range(0, len(temp)):
            if temp[i].HostName == select_host and temp[i].ServiceName == select_service:
                service_1.append(temp[i])
    print service_1

    return render_to_rsponse('TsinghuaCloudMonitor/monitor.html', {'service': service_1, 'usergroup': usergroup})


def hoststatus(request):
    # Redirect to login page if not logged in
    username = request.session['username']
    usergroup = request.session['usergroup']
    if username == None:
        return HttpResponseRedirect('/login')
    if username == '':
        return HttpResponseRedirect('/login')

    host = []
    maxhost = HostStatus.objects.all().values('HostName').annotate(max=Max('LastCheck')).filter(HostName__in=Host.objects.all().values('HostName'))
    for i in range(0, len(maxhost)):
        current_host = get_object_or_404(Host, HostName=maxhost[i].get('HostName'))
        # Only showing external host
        if current_host.HostType != 'external':
            continue
        # If user.group = user, show his own hosts. If user.group = admin, show all hosts.
        if usergroup == 'user' and current_host.Owner != username:
            continue
        temp = HostStatus.objects.filter(HostName=maxhost[i].get('HostName'), LastCheck=maxhost[i].get('max'))        # temp stores all hosts' info
        for i in range(0, len(temp)):
            temp[i].HostType = current_host.HostType
            status = temp[i].PluginOutput
            print status[0:5]
            if status[0:6] != 'PINGOK':
                temp[i].Status = 'DOWN'
            else:
                temp[i].Status = 'UP'
            print temp[i].HostType
            host.append(temp[i])

    return render(request, 'TsinghuaCloudMonitor/hoststatus.html', {'host': host, 'usergroup': usergroup})

def memory_external(request):
    # Redirect to login page if not logged in
    username = request.session['username']
    usergroup = request.session['usergroup']
    if username == None:
        return HttpResponseRedirect('/login')
    if username == '':
        return HttpResponseRedirect('/login')

    # Get parameters from URL
    cur_page_no = request.GET.get('page')
    filterby_user = request.GET.get('user')
    item_per_page = request.GET.get('pageelem')

    # Get a correct page no, filterby_user(if needed), item_per_page(if needed)
    if cur_page_no == '':
        cur_page_no = 1
    elif cur_page_no <= 0:
        cur_page_no = 1
    else:
        cur_page_no = int(cur_page_no)

    if filterby_user != '':
        if usergroup == 'user':                                         # Users can only get records of his own hosts
            filterby_user = username
    else:
        filterby_user = ''                                               # No filter has been set

    if item_per_page == None or item_per_page == '':
        item_per_page = 4
    else:
        item_per_page = int(item_per_page)
        if item_per_page <= 4:
            item_per_page = 4
        elif item_per_page >= 10:
            item_per_page = 4

    my_host_list = None
    # Get all user's hosts
    if usergroup == 'user':
        my_host_list = Host.objects.all().values('HostName', 'HostType').filter(HostType = 'external', Owner = username)
    # If usergroup = admin and with filterby_user set, show #filterby_user's hosts.
    elif usergroup == 'admin' and filterby_user != '':
        my_host_list = Host.objects.all().values('HostName', 'HostType').filter(HostType = 'external', Owner = filterby_user)
    # else (usergroup = admin and filterby_user == ''), show all hosts
    else:
        my_host_list = Host.objects.all().values('HostName', 'HostType').filter(HostType = 'external')

    host_count = len(my_host_list)
    start_pos = 0
    end_pos = 0
    print "host_count = " + str(host_count)

    # Get start and end of consulting host
    if (cur_page_no - 1) * item_per_page >= host_count:
        start_pos = 0
        if item_per_page > host_count:
            end_pos = host_count
        else:
            end_pos = item_per_page
    else:
        start_pos = (cur_page_no - 1) * item_per_page
        if start_pos + item_per_page > host_count:
            end_pos = host_count
        else:
            end_pos = start_pos + item_per_page
    print "start = " + str(start_pos) + ' | end = ' + str(end_pos)

    memory_name = ''
    memory_used = ''
    memory_total = ''
    memory_percentage = 0
    memory_json_obj = []
    # Get hosts' service records
    for i in range(start_pos, end_pos):
        # Get last check time for current host
        latest_check = Service.objects.values('HostName').annotate(LastCheck = Max('LastCheck'))\
            .filter(HostName = my_host_list[i].get('HostName'), ServiceName = 'MemoryUsage')

        # No record found.
        if len(latest_check) == 0:
            svc_rec_obj = None
        else:
            svc_rec_obj = get_object_or_404(Service, HostName = my_host_list[i].get('HostName'),ServiceName='MemoryUsage',
                                        LastCheck=latest_check[0].get('LastCheck'))

        # Form json object
        if svc_rec_obj == None:                               # Got no such host's record
            memory_name = my_host_list[i].get('HostName')
            memory_used = 0
            memory_total = 0
            memory_percentage = 0
        else:
            memory_name = my_host_list[i].get('HostName')
            if svc_rec_obj.PerformanceData == '':
                memory_used = 0
                memory_total = 0
                memory_percentage = 0
            else:
                p = re.compile(r'\d+')
                memory_used = p.findall(svc_rec_obj.PerformanceData)[1]
                memory_total = p.findall(svc_rec_obj.PerformanceData)[0]
                if memory_total == 0:
                    memory_percentage = 0
                else:
                    memory_percentage = format(float(memory_used) / float(memory_total), '.2%')
        json_data = {'name': memory_name, 'used': memory_used, 'total': memory_total, 'percentage': memory_percentage}
        memory_json_obj.append(json_data)

    return HttpResponse(json.dumps(memory_json_obj), content_type="application/json")


# Get external hosts' CPU operation records.
def cpu_external(request):
    # Redirect to login page if not logged in
    username = request.session['username']
    usergroup = request.session['usergroup']
    if username == None:
        return HttpResponseRedirect('/login')
    if username == '':
        return HttpResponseRedirect('/login')

    # Get parameters from URL
    cur_page_no = request.GET.get('page')
    filterby_user = request.GET.get('user')
    item_per_page = request.GET.get('pageelem')

    # Get a correct page no, filterby_user(if needed), item_per_page(if needed)
    if cur_page_no == None:
        cur_page_no = 1
    elif cur_page_no == '':
        cur_page_no = 1
    elif cur_page_no <= 0:
        cur_page_no = 1
    else:
        cur_page_no = int(cur_page_no)

    # Get a correct user filter
    if filterby_user== None:
        filterby_user = ''
    elif filterby_user == '':
        filterby_user = ''
    elif usergroup == 'user':                                         # Users can only get records of his own hosts
        filterby_user = username

    # Get a correct item_per_page
    if item_per_page == None:
        item_per_page = 4
    elif item_per_page == '':
        item_per_page = 4
    else:
        item_per_page = int(item_per_page)
        if item_per_page <= 4:
            item_per_page = 4
        elif item_per_page >= 10:
            item_per_page = 4

    my_host_list = None
    # Get all user's hosts
    if usergroup == 'user':
        my_host_list = Host.objects.all().values('HostName', 'HostType').filter(HostType = 'external', Owner = username)
    # If usergroup = admin and with filterby_user set, show #filterby_user's hosts.
    elif usergroup == 'admin' and filterby_user != '':
        my_host_list = Host.objects.all().values('HostName', 'HostType').filter(HostType = 'external', Owner = filterby_user)
    # else (usergroup = admin and filterby_user == ''), show all hosts
    else:
        my_host_list = Host.objects.all().values('HostName', 'HostType').filter(HostType = 'external')

    host_count = len(my_host_list)
    start_pos = 0
    end_pos = 0

    # Get start and end of consulting host
    if (cur_page_no - 1) * item_per_page >= host_count:
        start_pos = 0
        if item_per_page > host_count:
            end_pos = host_count
        else:
            end_pos = item_per_page
    else:
        start_pos = (cur_page_no - 1) * item_per_page
        if start_pos + item_per_page > host_count:
            end_pos = host_count
        else:
            end_pos = start_pos + item_per_page

    cpu_name = ''
    cpu_used = ''
    cpu_perc = ''
    cpu_json_obj = []
    # Get hosts' service records
    for i in range(start_pos, end_pos):
        # Get last check time for current host
        latest_check = Service.objects.values('HostName').annotate(LastCheck = Max('LastCheck'))\
            .filter(HostName = my_host_list[i].get('HostName'), ServiceName = 'cpuload')

        # No record found.
        if len(latest_check) == 0:
            svc_rec_obj = None
        else:
            svc_rec_obj = get_object_or_404(Service, HostName = my_host_list[i].get('HostName'),ServiceName='cpuload',
                                        LastCheck=latest_check[0].get('LastCheck'))

        # Form json object
        if svc_rec_obj == None:                               # Got no such host's record
            cpu_name = my_host_list[i].get('HostName')
            cpu_used = '0.0'
            cpu_perc = '0.0%'
        else:
            cpu_name = my_host_list[i].get('HostName')
            if svc_rec_obj.PerformanceData == '':
                cpu_used = '0.0'
                cpu_perc = '0.0%'
            else:
                p = re.compile(r'\d+')
                cpu_used = p.findall(svc_rec_obj.PerformanceData)[3]
                cpu_perc = format(float(cpu_used), '.2%')
        json_data = {'name': cpu_name, 'used': cpu_used, 'percentage': cpu_perc}
        cpu_json_obj.append(json_data)

    return HttpResponse(json.dumps(cpu_json_obj), content_type="application/json")

def pro_external(request):
    # Redirect to login page if not logged in
    username = request.session['username']
    usergroup = request.session['usergroup']
    if username == None:
        return HttpResponseRedirect('/login')
    if username == '':
        return HttpResponseRedirect('/login')

    # Get parameters from URL
    cur_page_no = request.GET.get('page')
    filterby_user = request.GET.get('user')
    item_per_page = request.GET.get('pageelem')

    # Get a correct page no, filterby_user(if needed), item_per_page(if needed)
    if cur_page_no == None:
        cur_page_no = 1
    elif cur_page_no == '':
        cur_page_no = 1
    elif cur_page_no <= 0:
        cur_page_no = 1
    else:
        cur_page_no = int(cur_page_no)
    
    # Get a correct user filter 
    if filterby_user== None:
        filterby_user = ''
    elif filterby_user == '':
        filterby_user = ''
    elif usergroup == 'user':                                         # Users can only get records of his own hosts
        filterby_user = username

    # Get a correct item_per_page
    if item_per_page == None:
        item_per_page = 4
    elif item_per_page == '':
        item_per_page = 4
    else:
        item_per_page = int(item_per_page)
        if item_per_page <= 4:
            item_per_page = 4
        elif item_per_page >= 10:
            item_per_page = 4

    my_host_list = None
    # Get all user's hosts
    if usergroup == 'user':
        print "ext+usr"
        my_host_list = Host.objects.all().values('HostName', 'HostType').filter(HostType = 'external', Owner = username)
    # If usergroup = admin and with filterby_user set, show #filterby_user's hosts.
    if usergroup == 'admin' and filterby_user != '':
        print "ext+admin+filter"
        my_host_list = Host.objects.all().values('HostName', 'HostType').filter(HostType = 'external', Owner = filterby_user)
    # else (usergroup = admin and filterby_user == ''), show all hosts
    else :
        print "ext+admin+nofilter"
        my_host_list = Host.objects.all().values('HostName', 'HostType').filter(HostType = 'external')

    host_count = len(my_host_list)
    start_pos = 0
    end_pos = 0
    print "host_count = " + str(host_count)

    # Get start and end of consulting host
    if (cur_page_no - 1) * item_per_page >= host_count:
        start_pos = 0
        if item_per_page > host_count:
            end_pos = host_count
        else:
            end_pos = item_per_page
    else:
        start_pos = (cur_page_no - 1) * item_per_page
        if start_pos + item_per_page > host_count:
            end_pos = host_count
        else:
            end_pos = start_pos + item_per_page
    print "start = " + str(start_pos) + ' | end = ' + str(end_pos)

    pro_name = ''
    pro_used = ''
    pro_json_obj = []
    # Get hosts' service records
    for i in range(start_pos, end_pos):
        # Get last check time for current host
        latest_check = Service.objects.values('HostName').annotate(LastCheck = Max('LastCheck'))\
            .filter(HostName = my_host_list[i].get('HostName'), ServiceName = 'total-procs')

        print latest_check
        print latest_check[0]
        print latest_check[0].get('LastCheck')
        # No record found.
        if len(latest_check) == 0:
            svc_rec_obj = None
        else:
            svc_rec_obj = get_object_or_404(Service, HostName = my_host_list[i].get('HostName'),ServiceName='total-procs',
                                        LastCheck=latest_check[0].get('LastCheck'))

        print 'svc.hostname = ' + svc_rec_obj.HostName
        if svc_rec_obj == None:                               # Got no such host's record
            pro_name = my_host_list[i].get('HostName')
            pro_used = '0.0'
        else:
            pro_name = my_host_list[i].get('HostName')
            if svc_rec_obj.PerformanceData == '':
                pro_used = '0.0'
            else:
                p = re.compile(r'\d+')
                pro_used = p.findall(svc_rec_obj.PerformanceData)[0]
        json_data = {'name': pro_name, 'used': pro_used}
        pro_json_obj.append(json_data)

    return HttpResponse(json.dumps(pro_json_obj), content_type="application/json")

def disk_external(request):
    # Redirect to login page if not logged in
    username = request.session['username']
    usergroup = request.session['usergroup']
    if username == None:
        return HttpResponseRedirect('/login')
    if username == '':
        return HttpResponseRedirect('/login')

    # Get parameters from URL
    cur_page_no = request.GET.get('page')
    filterby_user = request.GET.get('user')
    item_per_page = request.GET.get('pageelem')

    # Get a correct page no, filterby_user(if needed), item_per_page(if needed)
    if cur_page_no == None:
        cur_page_no = 1
    elif cur_page_no == '':
        cur_page_no = 1
    elif cur_page_no <= 0:
        cur_page_no = 1
    else:
        cur_page_no = int(cur_page_no)
    
    # Get a correct user filter 
    if filterby_user== None:
        filterby_user = ''
    elif filterby_user == '':
        filterby_user = ''
    elif usergroup == 'user':                                         # Users can only get records of his own hosts
        filterby_user = username

    print "filter = " + filterby_user

    # Get a correct item_per_page
    if item_per_page == None:
        item_per_page = 4
    elif item_per_page == '':
        item_per_page = 4
    else:
        item_per_page = int(item_per_page)
        if item_per_page <= 4:
            item_per_page = 4
        elif item_per_page >= 10:
            item_per_page = 4

    my_host_list = None
    # Get all user's hosts
    if usergroup == 'user':
        my_host_list = Host.objects.all().values('HostName', 'HostType').filter(HostType = 'external', Owner = username)
    # If usergroup = admin and with filterby_user set, show #filterby_user's hosts.
    elif usergroup == 'admin' and filterby_user != '':
        my_host_list = Host.objects.all().values('HostName', 'HostType').filter(HostType = 'external', Owner = filterby_user)
    # else (usergroup = admin and filterby_user == ''), show all hosts
    else:
        my_host_list = Host.objects.all().values('HostName', 'HostType').filter(HostType = 'external')

    host_count = len(my_host_list)
    start_pos = 0
    end_pos = 0
    print "host_count = " + str(host_count)

    # Get start and end of consulting host
    if (cur_page_no - 1) * item_per_page >= host_count:
        start_pos = 0
        if item_per_page > host_count:
            end_pos = host_count
        else:
            end_pos = item_per_page
    else:
        start_pos = (cur_page_no - 1) * item_per_page
        if start_pos + item_per_page > host_count:
            end_pos = host_count
        else:
            end_pos = start_pos + item_per_page
    print "start = " + str(start_pos) + ' | end = ' + str(end_pos)

    disk_name = ''
    disk_used = ''
    disk_total = ''
    disk_percentage = 0
    disk_json_obj = []
    # Get hosts' service records
    for i in range(start_pos, end_pos):
        # Get last check time for current host
        latest_check = Service.objects.values('HostName').annotate(LastCheck = Max('LastCheck'))\
            .filter(HostName = my_host_list[i].get('HostName'), ServiceName = 'disk')

        # No record found.
        if len(latest_check) == 0:
            svc_rec_obj = None
        else:
            svc_rec_obj = get_object_or_404(Service, HostName = my_host_list[i].get('HostName'),ServiceName='disk',
                                        LastCheck=latest_check[0].get('LastCheck'))

        if svc_rec_obj == None:                               # Got no such host's record
            disk_name = my_host_list[i].get('HostName')
            disk_used = 0
            disk_total = 0
            disk_percentage = 0
        else:
            disk_name = my_host_list[i].get('HostName')
            if svc_rec_obj.PerformanceData == '':
                disk_used = 0
                disk_total = 0
                disk_percentage = 0
            else:
                p = re.compile(r'\d+')
                disk_used = p.findall(svc_rec_obj.PerformanceData)[0]
                disk_total = p.findall(svc_rec_obj.PerformanceData)[4]
                if disk_total == 0:
                    disk_percentage = 0
                else:
                    disk_percentage = format(float(disk_used) / float(disk_total), '.2%')
        json_data = {'name': disk_name, 'used': disk_used, 'total': disk_total, 'percentage': disk_percentage}
        disk_json_obj.append(json_data)

    return HttpResponse(json.dumps(disk_json_obj), content_type="application/json")

def eth_external(request):
    # Redirect to login page if not logged in
    username = request.session['username']
    usergroup = request.session['usergroup']
    if username == None:
        return HttpResponseRedirect('/login')
    if username == '':
        return HttpResponseRedirect('/login')

    # Get parameters from URL
    cur_page_no = request.GET.get('page')
    filterby_user = request.GET.get('user')
    item_per_page = request.GET.get('pageelem')

    # Get a correct page no, filterby_user(if needed), item_per_page(if needed)
    if cur_page_no == None:
        cur_page_no = 1
    elif cur_page_no == '':
        cur_page_no = 1
    elif cur_page_no <= 0:
        cur_page_no = 1
    else:
        cur_page_no = int(cur_page_no)
    
    # Get a correct user filter 
    if filterby_user== None:
        filterby_user = ''
    elif filterby_user == '':
        filterby_user = ''
    elif usergroup == 'user':                                         # Users can only get records of his own hosts
        filterby_user = username

    print "filter = " + filterby_user

    # Get a correct item_per_page
    if item_per_page == None:
        item_per_page = 4
    elif item_per_page == '':
        item_per_page = 4
    else:
        item_per_page = int(item_per_page)
        if item_per_page <= 4:
            item_per_page = 4
        elif item_per_page >= 10:
            item_per_page = 4

    my_host_list = None
    # Get all user's hosts
    if usergroup == 'user':
        my_host_list = Host.objects.all().values('HostName', 'HostType').filter(HostType = 'external', Owner = username)
    # If usergroup = admin and with filterby_user set, show #filterby_user's hosts.
    elif usergroup == 'admin' and filterby_user != '':
        my_host_list = Host.objects.all().values('HostName', 'HostType').filter(HostType = 'external', Owner = filterby_user)
    # else (usergroup = admin and filterby_user == ''), show all hosts
    else:
        my_host_list = Host.objects.all().values('HostName', 'HostType').filter(HostType = 'external')

    host_count = len(my_host_list)
    start_pos = 0
    end_pos = 0
    print "host_count = " + str(host_count)

    # Get start and end of consulting host
    if (cur_page_no - 1) * item_per_page >= host_count:
        start_pos = 0
        if item_per_page > host_count:
            end_pos = host_count
        else:
            end_pos = item_per_page
    else:
        start_pos = (cur_page_no - 1) * item_per_page
        if start_pos + item_per_page > host_count:
            end_pos = host_count
        else:
            end_pos = start_pos + item_per_page
    print "start = " + str(start_pos) + ' | end = ' + str(end_pos)

    eth_name = ''
    eth_in = ''
    eth_out = ''
    eth_json_obj = []
    # Get hosts' service records
    for i in range(start_pos, end_pos):
        # Get last check time for current host
        print my_host_list[i].get('HostName')
        latest_check = Service.objects.values('HostName').annotate(last_check = Max('LastCheck'))\
            .filter(HostName = my_host_list[i].get('HostName'), ServiceName = 'Traffic_eth0')
        if len(latest_check) == 0:
            svc_rec_obj = None
        else:
            svc_rec_obj = get_object_or_404(Service, HostName = my_host_list[i].get('HostName'),ServiceName='Traffic_eth0',
                                        LastCheck=latest_check[0].get('last_check'))

        if svc_rec_obj == None:                               # Got no such host's record
            eth_name = my_host_list[i].get('HostName')
            eth_in = 0
            eth_out = 0
        else:
            eth_name = my_host_list[i].get('HostName')
            if svc_rec_obj.PerformanceData == '':
                eth_in = 0
                eth_out = 0
            else:
                p = re.compile(r'\d+')
                eth_in = p.findall(svc_rec_obj.PerformanceData)[0]
                eth_out = p.findall(svc_rec_obj.PerformanceData)[5]
        json_data = {'name': eth_name, 'in': eth_in, 'out': eth_out}
        eth_json_obj.append(json_data)

    return HttpResponse(json.dumps(eth_json_obj), content_type="application/json")

def totalcompare(request):
    if request.session['username'] == '':
        return HttpResponseRedirect('/login')

    username = request.session['username']
    usergroup = request.session['usergroup']
    memoryuse_name = []
    memoryuse_total = []
    memoryuse_used = []
    memoryuse_object = []
    memoryuse = []

    if usergroup == 'admin':
        # Show all hosts for admin
        memoryuse = Service.objects.all().values('ServiceName', 'HostName').annotate(max=Max('LastCheck')) \
            .filter(ServiceName='MemoryUsage', HostName__in=Host.objects.all().values('HostName'))
    elif usergroup == 'user':
        # Only showing user's hosts
        memoryuse = Service.objects.all().values('ServiceName', 'HostName').annotate(max=Max('LastCheck')) \
            .filter(ServiceName='MemoryUsage', HostName__in=Host.objects.all().values('HostName').filter(Owner = username))

    size = len(memoryuse)
    p = re.compile(r'\d+')
    for k in range(0, size):
        temp_first = Service.objects.all().filter(HostName=memoryuse[k].get('HostName'), ServiceName='MemoryUsage',
                                                  LastCheck=memoryuse[k].get('max'))

        if len(temp_first) > 1:
            temp = temp_first[0]
        else:
            temp = get_object_or_404(Service, HostName=memoryuse[k].get('HostName'), ServiceName='MemoryUsage',
                                     LastCheck=memoryuse[k].get('max'))
        memoryuse_name.append(temp.HostName)
        if temp.PerformanceData == '':
            memoryuse_used.append(0)
            memoryuse_total.append(0)
        else:
            memoryuse_used.append(p.findall(temp.PerformanceData)[1])
            memoryuse_total.append(p.findall(temp.PerformanceData)[0])
        if memoryuse_total[k] == 0:
            temp = 0
        else:
            temp = format(float(memoryuse_used[k]) / float(memoryuse_total[k]), '.2%')

        memoryuse_dic = {'name': memoryuse_name[k], 'used': memoryuse_used[k], 'total': memoryuse_total[k],
                         'percentage': temp}
        memoryuse_object.append(memoryuse_dic)

    cpuloaduse_name = []
    cpuloaduse_used = []
    cpuloaduse_object = []
    cpuloaduse = []

    if usergroup == 'admin':
        # Show all hosts for admin
        cpuloaduse = Service.objects.all().values('ServiceName', 'HostName').annotate(max=Max('LastCheck')) \
            .filter(ServiceName='cpuload', HostName__in=Host.objects.all().values('HostName'))
    elif usergroup == 'user':
        # Only showing user's hosts
        cpuloaduse = Service.objects.all().values('ServiceName', 'HostName').annotate(max=Max('LastCheck')) \
            .filter(ServiceName='cpuload', HostName__in=Host.objects.all().values('HostName').filter(Owner = username))

    size = len(cpuloaduse)
    p = re.compile(r'(\d+)\.(\d*)')
    for k in range(0, size):
        temp = get_object_or_404(Service, HostName=cpuloaduse[k].get('HostName'), ServiceName='cpuload',
                                 LastCheck=cpuloaduse[k].get('max'))
        cpuloaduse_name.append(temp.HostName)
        if temp.PerformanceData == '':
            cpuloaduse_used.append(0)
        else:
            cpuloaduse_used.append('.'.join(p.findall(temp.PerformanceData)[3]))

        tem = format(float(cpuloaduse_used[k]), '.2%')
        cpuloaduse_dic = {'name': cpuloaduse_name[k], 'used': cpuloaduse_used[k], 'percentage': tem}
        cpuloaduse_object.append(cpuloaduse_dic)

    diskusage_name = []
    diskusage_used = []
    diskusage_total = []
    diskusage_object = []
    diskusage = []

    if usergroup == 'admin':
        # Show all hosts for admin
        diskusage = Service.objects.all().values('ServiceName', 'HostName').annotate(max=Max('LastCheck')) \
            .filter(ServiceName='disk', HostName__in=Host.objects.all().values('HostName'))
    elif usergroup == 'user':
        # Only showing user's hosts
        diskusage = Service.objects.all().values('ServiceName', 'HostName').annotate(max=Max('LastCheck')) \
            .filter(ServiceName='disk', HostName__in=Host.objects.all().values('HostName').filter(Owner = username))

    size = len(diskusage)
    p = re.compile(r'\d+')
    for k in range(0, size):
        temp = get_object_or_404(Service, HostName=diskusage[k].get('HostName'), ServiceName='disk',
                                 LastCheck=diskusage[k].get('max'))
        diskusage_name.append(temp.HostName)
        if temp.PerformanceData == '':
            diskusage_used.append(0)
            diskusage_total.append(0)
        else:
            diskusage_used.append(p.findall(temp.PerformanceData)[0])
            diskusage_total.append(p.findall(temp.PerformanceData)[4])
        if diskusage_total[k] == 0:
            tem = 0
        else:
            tem = format(float(diskusage_used[k]) / float(diskusage_total[k]), '.2%')

        diskusage_dic = {'name': diskusage_name[k], 'used': diskusage_used[k], 'total': diskusage_total[k],
                         'percentage': tem}
        diskusage_object.append(diskusage_dic)

    pro_name = []
    pro_used = []
    processusage_object = []
    prousage = []

    if usergroup == 'admin':
        # Show all hosts for admin
        prousage = Service.objects.all().values('ServiceName', 'HostName').annotate(max=Max('LastCheck')) \
            .filter(ServiceName='total-procs', HostName__in=Host.objects.all().values('HostName'))
    elif usergroup == 'user':
        # Only showing user's hosts
        prousage = Service.objects.all().values('ServiceName', 'HostName').annotate(max=Max('LastCheck')) \
            .filter(ServiceName='total-procs', HostName__in=Host.objects.all().values('HostName').filter(Owner = username))

    size = len(prousage)
    p = re.compile(r'\d+')
    for k in range(0, size):
        temp = get_object_or_404(Service, HostName=prousage[k].get('HostName'), ServiceName='total-procs',
                                 LastCheck=prousage[k].get('max'))
        pro_name.append(temp.HostName)
        if temp.PerformanceData == '':
            pro_used.append(0)
        else:
            pro_used.append(p.findall(temp.PerformanceData)[0])
        processusage_dic = {'name': pro_name[k], 'used': pro_used[k]}
        processusage_object.append(processusage_dic)

    eth_name = []
    eth_in = []
    eth_out = []
    eth_object = []
    eth = []
    if usergroup == 'admin':
        # Show all hosts for admin
        eth = Service.objects.all().values('ServiceName', 'HostName').annotate(max=Max('LastCheck')) \
            .filter(ServiceName='Traffic_eth0', HostName__in=Host.objects.all().values('HostName'))
    elif usergroup == 'user':
        # Only showing user's hosts
        eth = Service.objects.all().values('ServiceName', 'HostName').annotate(max=Max('LastCheck')) \
            .filter(ServiceName='Traffic_eth0', HostName__in=Host.objects.all().values('HostName').filter(Owner = username))

    size = len(eth)
    p = re.compile(r'\d+')
    for k in range(0, size):
        temp = get_object_or_404(Service, HostName=eth[k].get('HostName'), ServiceName='Traffic_eth0',
                                 LastCheck=eth[k].get('max'))
        eth_name.append(temp.HostName)
        if temp.PerformanceData == '':
            eth_in.append(0)
            eth_out.append(0)
        else:
            eth_in.append(p.findall(temp.PerformanceData)[0])
            eth_out.append(p.findall(temp.PerformanceData)[5])
        eth_dic = {'name': eth_name[k], 'in': eth_in[k], 'out': eth_out[k]}
        eth_object.append(eth_dic)

    return render(request, 'TsinghuaCloudMonitor/totalcompare.html',
                  {'memoryuse_name': memoryuse_name, 'memoryuse_used': memoryuse_used,
                   'memoryuse_total': memoryuse_total, 'memoryuse_object': memoryuse_object,
                   'cpuloaduse_name': cpuloaduse_name, 'cpuloaduse_used': cpuloaduse_used,
                   'cpuloaduse_object': cpuloaduse_object, 'diskusage_name': diskusage_name,
                   'diskusage_used': diskusage_used, 'diskusage_total': diskusage_total,
                   'diskusage_object': diskusage_object, 'pro_name': pro_name, 'pro_used': pro_used,
                   'processusage_object': processusage_object, 'eth_name': eth_name, 'eth_in': eth_in,
                   'eth_out': eth_out, 'eth_object': eth_object, 'usergroup': usergroup})


def hostdetail(request, serviceid):
    # Redirect to login page if not logged in
    username = request.session['username']
    usergroup = request.session['usergroup']
    if username == None:
        return HttpResponseRedirect('/login')
    if username == '':
        return HttpResponseRedirect('/login')

    service = get_object_or_404(Service, pk=serviceid)
    host = get_object_or_404(Host, HostName=service.HostName)
    memory = Service.objects.filter(HostName=service.HostName, ServiceName='MemoryUsage')
    p = re.compile(r'\d+')
    memory_total = []
    memory_used = []
    memory_timestamp = []
    for k in range(len(memory) - 1, 0, -1):
        if p.findall(memory[k].PerformanceData):
            memory_total.append(p.findall(memory[k].PerformanceData)[0])
            if k == (len(memory) - 1):
                memory_used.append(p.findall(memory[k].PerformanceData)[1])
                memory_timestamp.append(memory[k].LastCheck)
            else:
                if memory[k].PerformanceData == '':
                    print 'ssss'
                    memory_used.append(0)
                    memory_timestamp.append(memory[k].LastCheck)
                else:
                    if (memory[k + 1].PerformanceData != '') and (
                                p.findall(memory[k].PerformanceData)[1] != p.findall(memory[k + 1].PerformanceData)[1]):
                        memory_used.append(p.findall(memory[k].PerformanceData)[1])
                        memory_timestamp.append(memory[k].LastCheck)
    print memory_timestamp
    print memory_used
    cpuload = Service.objects.filter(HostName=service.HostName, ServiceName='cpuload')
    p = re.compile(r'(\d+)\.(\d*)')
    cpu_one = []
    cpu_five = []
    cpu_timestamp = []
    for k in range(len(cpuload) - 1, 0, -1):
        if cpuload[k].PerformanceData == '':
            cpu_one.append(0)
            cpu_five.append(0)
            cpu_timestamp.append(cpuload[k].LastCheck)
        else:
            if k == (len(cpuload) - 1):
                cpu_one.append('.'.join(p.findall(cpuload[k].PerformanceData)[0]))
                cpu_five.append('.'.join(p.findall(cpuload[k].PerformanceData)[3]))
                cpu_timestamp.append(cpuload[k].LastCheck)

            else:
                if (cpuload[k + 1].PerformanceData != '') and (
                            '.'.join(p.findall(cpuload[k].PerformanceData)[0]) != '.'.join(
                                p.findall(cpuload[k + 1].PerformanceData)[0])):
                    cpu_one.append('.'.join(p.findall(cpuload[k].PerformanceData)[0]))
                    cpu_five.append('.'.join(p.findall(cpuload[k].PerformanceData)[3]))
                    cpu_timestamp.append(cpuload[k].LastCheck)

    disk = Service.objects.filter(HostName=service.HostName, ServiceName='disk')
    p = re.compile(r'\d+')
    diskuse = []
    disk_timestamp = []
    for k in range(len(disk) - 1, 0, -1):
        if disk[k].PerformanceData == '':
            diskuse.append(0)
            disk_timestamp.append(disk[k].LastCheck)

        else:
            if k == (len(disk) - 1):
                diskuse.append(p.findall(disk[k].PerformanceData)[0])
                disk_timestamp.append(disk[k].LastCheck)
            else:
                if (disk[k + 1].PerformanceData != '') and (
                            p.findall(disk[k].PerformanceData)[0] != p.findall(disk[k + 1].PerformanceData)[0]):
                    diskuse.append(p.findall(disk[k].PerformanceData)[0])
                    disk_timestamp.append(disk[k].LastCheck)

    process = Service.objects.filter(HostName=service.HostName, ServiceName='total-procs')
    p = re.compile(r'\d+')
    pro = []
    pro_timestamp = []
    for k in range(len(process) - 1, 0, -1):
        if process[k].PerformanceData == '':
            pro.append(0)
            pro_timestamp.append(process[k].LastCheck)

        else:
            pro.append(p.findall(process[k].PerformanceData)[0])
            pro_timestamp.append(process[k].LastCheck)

    if host:
        return render_to_response('TsinghuaCloudMonitor/hostdetail.html',
                                  {'host': host, 'memory_total': memory_total, 'memory_used': memory_used,
                                   'memory_timestamp': memory_timestamp, 'cpu_one': cpu_one, 'cpu_five': cpu_five,
                                   'cpu_timestamp': cpu_timestamp, 'diskuse': diskuse, 'disk_timestamp': disk_timestamp,
                                   'pro': pro, 'pro_timestamp': pro_timestamp})
    else:
        return HttpResponse("ERROR")


def hostdetailmore(request, hostid):
    # Redirect to login page if not logged in
    username = request.session['username']
    usergroup = request.session['usergroup']
    if username == None:
        return HttpResponseRedirect('/login')
    if username == '':
        return HttpResponseRedirect('/login')

    hoststatus = get_object_or_404(HostStatus, pk=hostid)
    host = get_object_or_404(Host, HostName=hoststatus.HostName)
    memory = Service.objects.filter(HostName=host.HostName, ServiceName='MemoryUsage')
    p = re.compile(r'\d+')
    memory_total = []
    memory_used = []
    memory_timestamp = []
    for k in range(len(memory) - 1, 0, -1):
        if p.findall(memory[k].PerformanceData):
            memory_total.append(p.findall(memory[k].PerformanceData)[0])
            if memory[k].PerformanceData == '':
                memory_used.append(0)
                memory_timestamp.append(memory[k].LastCheck)
            else:
                if k == (len(memory) - 1):
                    memory_used.append(p.findall(memory[k].PerformanceData)[1])
                    memory_timestamp.append(memory[k].LastCheck)

                else:
                    if (memory[k + 1].PerformanceData != '') and (
                                p.findall(memory[k].PerformanceData)[1] != p.findall(memory[k + 1].PerformanceData)[1]):
                        memory_used.append(p.findall(memory[k].PerformanceData)[1])
                        memory_timestamp.append(memory[k].LastCheck)
    print memory_timestamp
    print memory_used

    cpuload = Service.objects.filter(HostName=host.HostName, ServiceName='cpuload')
    p = re.compile(r'(\d+)\.(\d*)')
    cpu_one = []
    cpu_five = []
    cpu_timestamp = []
    for k in range(len(cpuload) - 1, 0, -1):
        if cpuload[k].PerformanceData == '':
            cpu_one.append(0)
            cpu_five.append(0)
            cpu_timestamp.append(cpuload[k].LastCheck)
        else:
            if k == (len(cpuload) - 1):
                cpu_one.append('.'.join(p.findall(cpuload[k].PerformanceData)[0]))
                cpu_five.append('.'.join(p.findall(cpuload[k].PerformanceData)[3]))
                cpu_timestamp.append(cpuload[k].LastCheck)


            else:
                if (cpuload[k + 1].PerformanceData != '') and (
                            '.'.join(p.findall(cpuload[k].PerformanceData)[0]) != '.'.join(
                                p.findall(cpuload[k + 1].PerformanceData)[0])):
                    cpu_one.append('.'.join(p.findall(cpuload[k].PerformanceData)[0]))
                    cpu_five.append('.'.join(p.findall(cpuload[k].PerformanceData)[3]))
                    cpu_timestamp.append(cpuload[k].LastCheck)

    disk = Service.objects.filter(HostName=host.HostName, ServiceName='disk')
    p = re.compile(r'\d+')
    diskuse = []
    disk_timestamp = []
    for k in range(len(disk) - 1, 0, -1):
        if disk[k].PerformanceData == '':
            diskuse.append(0)
            disk_timestamp.append(disk[k].LastCheck)

        else:
            if k == (len(disk) - 1):
                diskuse.append(p.findall(disk[k].PerformanceData)[0])
                disk_timestamp.append(disk[k].LastCheck)
            else:
                if (disk[k + 1].PerformanceData != '') and (
                            p.findall(disk[k].PerformanceData)[0] != p.findall(disk[k + 1].PerformanceData)[0]):
                    diskuse.append(p.findall(disk[k].PerformanceData)[0])
                    disk_timestamp.append(disk[k].LastCheck)

    process = Service.objects.filter(HostName=host.HostName, ServiceName='total-procs')
    p = re.compile(r'\d+')
    pro = []
    pro_timestamp = []
    for k in range(len(process) - 1, 0, -1):
        if process[k].PerformanceData == '':
            pro.append(0)
            pro_timestamp.append(process[k].LastCheck)

        else:
            pro.append(p.findall(process[k].PerformanceData)[0])
            pro_timestamp.append(process[k].LastCheck)

    if host:
        return render_to_response('TsinghuaCloudMonitor/hostdetail.html',
                                  {'host': host, 'memory_total': memory_total, 'memory_used': memory_used,
                                   'memory_timestamp': memory_timestamp, 'cpu_one': cpu_one, 'cpu_five': cpu_five,
                                   'cpu_timestamp': cpu_timestamp, 'diskuse': diskuse, 'disk_timestamp': disk_timestamp,
                                   'pro': pro, 'pro_timestamp': pro_timestamp})
    else:
        return HttpResponse("ERROR")


def login(request):
    errors = []
    account = None
    password = None
    if request.method == 'POST':
        print "1"
        if not request.POST.get('account'):
            print "2"
            errors.append('Please Enter account')
        else:
            print "3"
            username = request.POST.get('account')
        if not request.POST.get('password'):
            print "4"
            errors.append('Please Enter password')
        else:
            print "5"
            password = request.POST.get('password')
            userObj = User.objects.filter(username=username,
                                          password=password)  # Look up if such username with password exists
            print username + " | " + password
            print len(userObj)
            # user = auth.authenticate(username = username, password = password)
            if len(userObj) != 0:  # Find a match of username and password
                user = userObj[0]
                request.session['username'] = user.username
                request.session['usergroup'] = user.usergroup
                return HttpResponseRedirect('/hoststatus')

            else:
                errors.append('invaild user')
                return HttpResponseRedirect('/login')

    return render_to_response('TsinghuaCloudMonitor/login.html', {'errors': errors})


def register(request):
    print "register_page"
    errors = []
    account = None
    password = None
    password2 = None
    CompareFlag = False
    ExistFlag = True

    if request.method == 'POST':
        if not request.POST.get('account'):
            errors.append('Please Enter account')
        else:
            account = request.POST.get('account')
        if not request.POST.get('password'):
            errors.append('Please Enter password')
        else:
            password = request.POST.get('password')
        if not request.POST.get('password2'):
            errors.append('Please Enter password2')
        else:
            password2 = request.POST.get('password2')

        # Test if passwords match
        if password and password2:
            if password == password2:
                CompareFlag = True
            else:
                errors.append('password2 is diff password ')

        # Test if username exists
        same_user = User.objects.filter(username = account)
        print same_user
        if len(same_user) == 0:
            ExistFlag = False
        else:
            errors.append('Username exists.')

        if account and password and password2 and CompareFlag and (not ExistFlag):
            user = User(username=account, password=password, usergroup = 'user')
            user.save()
            return HttpResponseRedirect('/login')

    return render_to_response('TsinghuaCloudMonitor/register.html', {'errors': errors})


def start_input(request):
    # Redirect to login page if not logged in
    username = request.session['username']
    usergroup = request.session['usergroup']
    if username == '':
        return HttpResponseRedirect('/login')

    # No host input page for admin
    if usergroup == 'admin':
        return HttpResponseRedirect('/hoststatus')

    errors = []
    ip = None
    hostname = None
    if request.method == 'POST':
        if not request.POST.get('ip'):
            errors.append('Please Enter IP address')
        else:
            ip = request.POST.get('ip')
            print('dd')
        if not request.POST.get('hostname'):
            errors.append('Please Enter hostname')
        else:
            hostname = request.POST.get('hostname')

        now = time.time()
        print now
        print request.session['username']
        schedule = Schedule(IP=ip, HostName=hostname, ArrivingTime=now, Owner=request.session['username'])
        schedule.save()
        # p = sub.Popen('/home/django/TsinghuaCloud/TsinghuaCloud/schedule.py',stdout=sub.PIPE,shell=True)
        return HttpResponseRedirect('/hoststatus')

    return render_to_response('TsinghuaCloudMonitor/start_input.html', {'errors': errors})


def logout(request):
    request.session['username'] = None
    request.session['group'] = None
    return HttpResponseRedirect('/login')


def download_first(request):
    # do something...
    # Return to Login page if user's not logged in
    if request.session['username'] == '':
        return HttpResponseRedirect('/login')
    def file_iterator(file_name, chunk_size=512):
        with open(file_name) as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c

                else:
                    break

    the_file_name = "installation.sh"
    response = StreamingHttpResponse(file_iterator(the_file_name))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(the_file_name)

    return response


def download_second(request):
    # do something...
    # Return to Login page if user's not logged in
    if request.session['username'] == '':
        return HttpResponseRedirect('/login')
    def file_iterator(file_name, chunk_size=512):
        with open(file_name) as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c

                else:
                    break

    the_file_name = "nagios-plugins-2.0.tar.gz"
    response = StreamingHttpResponse(file_iterator(the_file_name))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(the_file_name)

    return response


def download_third(request):
    # do something...
    # Return to Login page if user's not logged in
    if request.session['username'] == '':
        return HttpResponseRedirect('/login')

    def file_iterator(file_name, chunk_size=512):
        with open(file_name) as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c

                else:
                    break

    the_file_name = "nrpe-2.14.tar.gz"
    response = StreamingHttpResponse(file_iterator(the_file_name))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(the_file_name)

    return response
  

