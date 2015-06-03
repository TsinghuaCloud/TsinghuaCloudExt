from django.db import models
import json
# Create your models here.

class User(models.Model):
    username = models.CharField(max_length=50)                  #
    password = models.CharField(max_length=50)                  #
    usergroup = models.CharField(max_length = 50)                   # user group: user | administrator
    
class Service(models.Model):
    ServiceName = models.CharField(max_length=50)               # Description of service
    HostName = models.CharField(max_length=50)                  # The host where service record got from
    Status = models.CharField(max_length=50)                    # Status of the host
    Attempt = models.CharField(max_length=50)
    Duration = models.CharField(max_length=50)
    PluginOutput = models.CharField(max_length=100)
    PerformanceData = models.CharField(max_length=100)          #
    LastCheck = models.CharField(max_length=50)                 # Last check date
    HostType = models.CharField(max_length=50)                  # (Typically NULL if not initialized)
    
class HostStatus(models.Model):
    HostName = models.CharField(max_length=50)
    PluginOutput = models.CharField(max_length=50)
    Duration = models.CharField(max_length=50)
    PerformanceData = models.CharField(max_length=100)
    LastCheck = models.CharField(max_length=50)
    HostType = models.CharField(max_length=50)
    Status = models.CharField(max_length=50)


class Host(models.Model):
    IP = models.CharField(max_length=50)
    HostName = models.CharField(max_length=50)
    Owner = models.CharField(max_length=50)
    Info = models.CharField(max_length=50)
    NagiosServer = models.CharField(max_length=50)
    HostType = models.CharField(max_length=50)

class Schedule(models.Model):
    IP = models.CharField(max_length=50)
    HostName = models.CharField(max_length=50)
    ArrivingTime = models.CharField(max_length=50)
    Owner = models.CharField(max_length = 50)

class Nagios(models.Model):
    Server = models.CharField(max_length=50)
    Target_IP =models.CharField(max_length=50)
    Target_HostName = models.CharField(max_length=50)
    
   

    
    



    
