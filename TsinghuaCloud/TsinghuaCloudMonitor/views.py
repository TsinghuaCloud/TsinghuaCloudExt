import base64, urllib, httplib, json, os, math
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
from TsinghuaCloudMonitor.models import Nagios

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
    username = ''
    try:
        username = request.session['username']
    except:
        print "username error" +  str(Exception)
    if username == '' or username == None:
        return HttpResponseRedirect('/login')
    usergroup = request.session['usergroup']

    flag = 1
    return render(request, 'TsinghuaCloudMonitor/submap.html', {'flag': flag, 'tenantid': tenantid})


@csrf_exempt
def start_system(request):
    # Redirect to login page if not logged in
    username = ''
    try:
        username = request.session['username']
    except:
        print "username error" +  str(Exception)
    if username == '' or username == None:
        return HttpResponseRedirect('/login')
    usergroup = request.session['usergroup']

    return render(request, 'TsinghuaCloudMonitor/start_system.html')


def start_input(request):
    # Redirect to login page if not logged in
    username = ''
    try:
        username = request.session['username']
    except:
        print "username error" +  str(Exception)
    if username == '' or username == None:
        return HttpResponseRedirect('/login')
    usergroup = request.session['usergroup']

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

def schedule_data(request):
        # Redirect to login page if not logged in
    username = ''
    try:
        username = request.session['username']
    except:
        print "username error" +  str(Exception)
    if username == '' or username == None:
        return HttpResponseRedirect('/login')
    usergroup = request.session['usergroup']

    # Refuse all user(not admin)s' requests
    if usergroup != 'admin':
        return HttpResponseRedirect('/hoststatus')

    # Get all hosts
    host_list = Host.objects.values('HostName').filter(HostType='external')

    # Get all monitor servers
    nagios_monitors = Nagios.objects.values('Server').distinct()
    print "nagios servers = " + str(len(nagios_monitors))

    # Monitor server records stored in server_table
    server_table = []
    for server in nagios_monitors:
        server_rec = {'ServerName': server.get('Server'), 'Host': []}
        server_table.append(server_rec)

    monitor_list = Nagios.objects.filter(Target_HostName__in=host_list)
    for monitor_item in monitor_list:
        for server_rec in server_table:
            if server_rec['ServerName'] == monitor_item.Server:
                server_rec['Host'].append(monitor_item.Target_IP)

    print server_table
    return HttpResponse(json.dumps(server_table), content_type="application/json")

def check_schedule(request):
    # Redirect to login page if not logged in
    username = ''
    try:
        username = request.session['username']
    except:
        print "username error" +  str(Exception)
    if username == '' or username == None:
        return HttpResponseRedirect('/login')
    usergroup = request.session['usergroup']

    # Refuse all user(not admin)s' requests
    if usergroup != 'admin':
        return HttpResponseRedirect('/hoststatus')

    # Get all hosts
    host_list = Host.objects.values('HostName').filter(HostType='external')

    # Get all monitor servers
    nagios_monitors = Nagios.objects.values('Server').distinct()
    print "nagios servers = " + str(len(nagios_monitors))

    # Monitor server records stored in server_table
    server_table = []
    for server in nagios_monitors:
        server_rec = {'ServerName': server.get('Server'), 'Host': []}
        server_table.append(server_rec)

    monitor_list = Nagios.objects.filter(Target_HostName__in=host_list)
    for monitor_item in monitor_list:
        for server_rec in server_table:
            if server_rec['ServerName'] == monitor_item.Server:
                server_rec['Host'].append(monitor_item.Target_IP)

    print server_table
    return render(request, 'TsinghuaCloudMonitor/schedule.html', {'server_table': server_table })

def monitor(request):
    # Redirect to login page if not logged in
    username = ''
    try:
        username = request.session['username']
    except:
        print "username error" +  str(Exception)
    if username == '' or username == None:
        return HttpResponseRedirect('/login')
    usergroup = request.session['usergroup']

    # Get hosts belonging to username
    monitor_host_list = Host.objects.all().values('id', 'HostName').filter(HostType='external')
    if usergroup == 'user':                                         # Users can only get records of his own hosts
        monitor_host_list = monitor_host_list.filter(Owner=username)
    host_count = len(monitor_host_list)
    print "host_count = " + str(host_count)

    # Get service records for each host

    service_table = []
    print "Run to 1"
    for k in range(0, host_count):
        print "Run to 2"
        last_check_rec_list = Service.objects.values('HostId', 'ServiceName').filter(HostId=monitor_host_list[k].get('id'), id__gt=700000).distinct()
        print "Run to 3"
        if len(last_check_rec_list) == 0:
            # Create empty service record
            service_na = Service()
            service_na.ServiceName = 'N/A'
            service_na.LastCheck = 'N/A'
            service_na.Duration = 0
            service_na.PerformanceData = 'N/A'
            service_na.PluginOutput = 'N/A'
            service_na.HostId = monitor_host_list[k].get('id')
            service_na.HostName = monitor_host_list[k].get('HostName')
            service_table.append(service_na)
        for single_last_check in last_check_rec_list:
            print "Run to 4"
            cur_id = monitor_host_list[k].get('id')
            svc_name = single_last_check.get('ServiceName')
            service_record = Service.objects.all().filter(HostId=cur_id, ServiceName=svc_name, id__gt=700000).last()
            print "Run to 5a"
            service_table.append(service_record)
            print "Run to 5b"

    print "Run to 6"
    # print service
    return render(request, 'TsinghuaCloudMonitor/monitor.html', {'service': service_table, 'usergroup': usergroup})


def doSearch(request):
    # Redirect to login page if not logged in
    username = ''
    try:
        username = request.session['username']
    except:
        print "username error" +  str(Exception)
    if username == '' or username == None:
        return HttpResponseRedirect('/login')
    usergroup = request.session['usergroup']

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

    return render_to_response('TsinghuaCloudMonitor/monitor.html', {'service': service_1, 'usergroup': usergroup})


def hoststatus(request):
    # Redirect to login page if not logged in
    username = ''
    try:
        username = request.session['username']
    except:
        print "username error" +  str(Exception)
    if username == '' or username == None:
        return HttpResponseRedirect('/login')
    usergroup = request.session['usergroup']

    # Get hosts belonging to username
    host_list = Host.objects.all().values('id', 'HostName').filter(HostType='external')
    if usergroup == 'user':                                         # Users can only get records of his own hosts
        host_list = host_list.filter(Owner=username)
    host_count = len(host_list)

    print "Run to 1"
    # Get status records for each host
    host_status_rec_obj = []
    for cur_host in host_list:
        check_record = HostStatus.objects.filter(HostId=cur_host.get('id')).last()
        if check_record == None:
            empty_status_rec = HostStatus()
            empty_status_rec.HostName = cur_host.get('HostName')
            empty_status_rec.HostId = 0
            empty_status_rec.Status = 'N/A'
            empty_status_rec.LastCheck = 'N/A'
            empty_status_rec.PluginOutput = 'N/A'
            empty_status_rec.Duration = '0'
            host_status_rec_obj.append(empty_status_rec)
            print "added"
        else:
            host_status_rec_obj.append(check_record)

    return render(request, 'TsinghuaCloudMonitor/hoststatus.html', {'host': host_status_rec_obj, 'usergroup': usergroup})

def memory_external(request):
    # Redirect to login page if not logged in
    username = ''
    try:
        username = request.session['username']
    except:
        print "username error" +  str(Exception)
    if username == '' or username == None:
        return HttpResponseRedirect('/login')
    usergroup = request.session['usergroup']
    print usergroup

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

    # Get a correct user filter
    if filterby_user== None:
        filterby_user = ''
    elif filterby_user == '':
        filterby_user = ''
    elif usergroup == 'user':                                         # Users can only get records of his own hosts
        filterby_user = username

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
    total_page = math.ceil(float(host_count) / float(item_per_page))
    print host_count
    print item_per_page
    print total_page

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

    memory_name = ''
    memory_used = ''
    memory_total = ''
    memory_percentage = 0
    memory_list = []
    memory_json = {}
    # Get hosts' service records
    for i in range(start_pos, end_pos):
        # Get last check time for current host
        latest_check = Service.objects.filter(HostName = my_host_list[i].get('HostName'), ServiceName = 'MemoryUsage')\
            .last()
        # Form json object
        if latest_check == None:                               # Got no such host's record
            memory_name = my_host_list[i].get('HostName')
            memory_used = 0
            memory_total = 0
            memory_percentage = 0
        else:
            memory_name = my_host_list[i].get('HostName')
            if latest_check.PerformanceData == '':
                memory_used = 0
                memory_total = 0
                memory_percentage = 0
            else:
                p = re.compile(r'\d+')
                memory_used = p.findall(latest_check.PerformanceData)[1]
                memory_total = p.findall(latest_check.PerformanceData)[0]
                if memory_total == 0:
                    memory_percentage = 0
                else:
                    memory_percentage = format(float(memory_used) / float(memory_total), '.2%')
        json_data = {'name': memory_name, 'used': memory_used, 'total': memory_total, 'percentage': memory_percentage}
        memory_list.append(json_data)

    memory_json['totalpage'] = int(total_page)
    memory_json['memorylist'] = memory_list

    return HttpResponse(json.dumps(memory_json), content_type="application/json")


# Get external hosts' CPU operation records.
def cpu_external(request):
    # Redirect to login page if not logged in
    username = ''
    try:
        username = request.session['username']
    except:
        print "username error" +  str(Exception)
    if username == '' or username == None:
        return HttpResponseRedirect('/login')
    usergroup = request.session['usergroup']

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
        my_host_list = Host.objects.values('HostName', 'HostType').filter(HostType = 'external', Owner = username)
    # If usergroup = admin and with filterby_user set, show #filterby_user's hosts.
    elif usergroup == 'admin' and filterby_user != '':
        my_host_list = Host.objects.values('HostName', 'HostType').filter(HostType = 'external', Owner = filterby_user)
    # else (usergroup = admin and filterby_user == ''), show all hosts
    else:
        my_host_list = Host.objects.values('HostName', 'HostType').filter(HostType = 'external')

    host_count = len(my_host_list)
    start_pos = 0
    end_pos = 0
    total_page = math.ceil(float(host_count) / float(item_per_page))

    # Get starting and ending number of consulting host
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
    cpu_list = []
    cpu_json = {}
    # Get hosts' service records
    for i in range(start_pos, end_pos):
        # Get last check time for current host
        latest_check = Service.objects.filter(HostName = my_host_list[i].get('HostName'), ServiceName = 'cpuload')\
            .last()

         # Form json object
        if latest_check == None:                               # Got no such host's record
            cpu_name = my_host_list[i].get('HostName')
            cpu_used = '0.0'
            cpu_perc = '0.0%'
        else:
            cpu_name = my_host_list[i].get('HostName')
            if latest_check.PerformanceData == '':
                cpu_used = '0.0'
                cpu_perc = '0.0%'
            else:
                p = re.compile(r'0\.\d+')
                cpu_used = p.findall(latest_check.PerformanceData)[0]
                cpu_perc = format(float(cpu_used), '.2%')
        json_data = {'name': cpu_name, 'used': cpu_used, 'percentage': cpu_perc}
        cpu_list.append(json_data)

    cpu_json['totalpage'] = int(total_page)
    cpu_json['cpulist'] = cpu_list
    return HttpResponse(json.dumps(cpu_json), content_type="application/json")

def pro_external(request):
    # Redirect to login page if not logged in
    username = ''
    try:
        username = request.session['username']
    except:
        print "username error" +  str(Exception)
    if username == '' or username == None:
        return HttpResponseRedirect('/login')
    usergroup = request.session['usergroup']

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
    else :
        my_host_list = Host.objects.all().values('HostName', 'HostType').filter(HostType = 'external')

    host_count = len(my_host_list)
    start_pos = 0
    end_pos = 0
    total_page = math.ceil(float(host_count) / float(item_per_page))

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
    pro_list = []
    pro_json = {}
    # Get hosts' service records
    for i in range(start_pos, end_pos):
        # Get last check time for current host
        latest_check = Service.objects.filter(HostName = my_host_list[i].get('HostName'), ServiceName = 'total-procs')\
            .last()
        if latest_check == None:                               # Got no such host's record
            pro_name = my_host_list[i].get('HostName')
            pro_used = '0.0'
        else:
            pro_name = my_host_list[i].get('HostName')
            if latest_check.PerformanceData == '':
                pro_used = '0.0'
            else:
                p = re.compile(r'\d+')
                pro_used = p.findall(latest_check.PerformanceData)[0]
        json_data = {'name': pro_name, 'used': pro_used}
        pro_list.append(json_data)

    pro_json['totalpage'] = int(total_page)
    pro_json['prolist'] = pro_list

    return HttpResponse(json.dumps(pro_json), content_type="application/json")

def disk_external(request):
    # Redirect to login page if not logged in
    username = ''
    try:
        username = request.session['username']
    except:
        print "username error" +  str(Exception)
    if username == '' or username == None:
        return HttpResponseRedirect('/login')
    usergroup = request.session['usergroup']


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
    total_page = math.ceil(float(host_count) / float(item_per_page))

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
    disk_list = []
    disk_json = {}
    # Get hosts' service records
    for i in range(start_pos, end_pos):
        # Get last check time for current host
        latest_check = Service.objects.filter(HostName = my_host_list[i].get('HostName'), ServiceName = 'disk')\
            .last()
        if latest_check == None:                               # Got no such host's record
            disk_name = my_host_list[i].get('HostName')
            disk_used = 0
            disk_total = 0
            disk_percentage = 0
        else:
            disk_name = my_host_list[i].get('HostName')
            if latest_check.PerformanceData == '':
                disk_used = 0
                disk_total = 0
                disk_percentage = 0
            else:
                p = re.compile(r'\d+')
                disk_used = p.findall(latest_check.PerformanceData)[0]
                disk_total = p.findall(latest_check.PerformanceData)[4]
                if disk_total == 0:
                    disk_percentage = 0
                else:
                    disk_percentage = format(float(disk_used) / float(disk_total), '.2%')
        json_data = {'name': disk_name, 'used': disk_used, 'total': disk_total, 'percentage': disk_percentage}
        disk_list.append(json_data)

    disk_json['totalpage'] = int(total_page)
    disk_json['disklist'] = disk_list

    return HttpResponse(json.dumps(disk_json), content_type="application/json")

def eth_external(request):
    # Redirect to login page if not logged in
    username = ''
    try:
        username = request.session['username']
    except:
        print "username error" +  str(Exception)
    if username == '' or username == None:
        return HttpResponseRedirect('/login')
    usergroup = request.session['usergroup']

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
    total_page = math.ceil(float(host_count) / float(item_per_page))

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
    eth_list = []
    eth_json = {}
    # Get hosts' service records
    for i in range(start_pos, end_pos):
        # Get last check time for current host
        print my_host_list[i].get('HostName')
        latest_check = Service.objects.filter(HostName = my_host_list[i].get('HostName'), ServiceName = 'Traffic_eth0')\
            .last()
        if latest_check == None:                               # Got no such host's record
            eth_name = my_host_list[i].get('HostName')
            eth_in = 0
            eth_out = 0
        else:
            eth_name = my_host_list[i].get('HostName')
            if latest_check.PerformanceData == '':
                eth_in = 0
                eth_out = 0
            else:
                p = re.compile(r'\d+')
                eth_in = p.findall(latest_check.PerformanceData)[0]
                eth_out = p.findall(latest_check.PerformanceData)[5]
        json_data = {'name': eth_name, 'in': eth_in, 'out': eth_out}
        eth_list.append(json_data)

    eth_json['totalpage'] = int(total_page)
    eth_json['ethlist'] = eth_list

    return HttpResponse(json.dumps(eth_json), content_type="application/json")

def totalcompare(request):
    # Redirect to login page if not logged in
    username = ''
    try:
        username = request.session['username']
    except:
        print "username error" +  str(Exception)
        return HttpResponseRedirect('/login')
    if username == '' or username == None:
        return HttpResponseRedirect('/login')

    # username = request.session['username']
    usergroup = request.session['usergroup']

    my_host_list = None
    # Get all user's hosts
    if usergroup == 'user':
        my_host_list = Host.objects.all().values('HostName', 'HostType').filter(HostType = 'external', Owner = username)
    # If usergroup = admin and with filterby_user set, show #filterby_user's hosts.
    elif usergroup == 'admin':
        my_host_list = Host.objects.all().values('HostName', 'HostType').filter(HostType = 'external')

    total_page = math.ceil(float(len(my_host_list)) / 4)

    return render(request, 'TsinghuaCloudMonitor/totalcompare.html',  {'usergroup': usergroup, 'totalpage': total_page})


def hostdetail(request, hostid):
    # Redirect to login page if not logged in
    username = ''
    try:
        username = request.session['username']
    except:
        print "username error" +  str(Exception)
    if username == '' or username == None:
        return HttpResponseRedirect('/login')
    usergroup = request.session['usergroup']

    host = get_object_or_404(Host, pk=hostid)
    memory = Service.objects.filter(HostId=host.id, ServiceName='MemoryUsage', id__gt=700000)
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
    cpuload = Service.objects.filter(HostId=host.id, ServiceName='cpuload', id__gt=700000)
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

    disk = Service.objects.filter(HostId=host.id, ServiceName='disk', id__gt=700000)
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

    process = Service.objects.filter(HostId=host.id, ServiceName='total-procs', id__gt=700000)
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
                                   'pro': pro, 'pro_timestamp': pro_timestamp, 'usergroup': usergroup})
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
    username = ''
    try:
        username = request.session['username']
    except:
        print "username error" +  str(Exception)
    if username == '' or username == None:
        return HttpResponseRedirect('/login')
    usergroup = request.session['usergroup']


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
    # Redirect to login page if not logged in
    username = ''
    try:
        username = request.session['username']
    except:
        print "username error" +  str(Exception)
    if username == '' or username == None:
        return HttpResponseRedirect('/login')
    usergroup = request.session['usergroup']

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
    # Redirect to login page if not logged in
    username = ''
    try:
        username = request.session['username']
    except:
        print "username error" +  str(Exception)
    if username == '' or username == None:
        return HttpResponseRedirect('/login')
    usergroup = request.session['usergroup']

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
    # Redirect to login page if not logged in
    username = ''
    try:
        username = request.session['username']
    except:
        print "username error" +  str(Exception)
    if username == '' or username == None:
        return HttpResponseRedirect('/login')
    usergroup = request.session['usergroup']

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
