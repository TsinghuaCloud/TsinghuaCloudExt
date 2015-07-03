#! /usr/bin/python
import pxssh  
import pexpect
import MySQLdb
import MySQLdb.cursors
import os
import os.path
import time

host1='192.168.173.22'
host2='192.168.173.23'
port='22'
username='root'
passwd='ubuntu'
cmd='/usr/local/nagios/etc/Configuration.py'

class DBConn:
    conn = None

    def connect(self):
        self.conn= MySQLdb.connect(
            host='166.111.143.241',
            port = 3306,
            user='root',
            passwd='tsinghua',
            db ='monitorService',
            cursorclass = MySQLdb.cursors.DictCursor
            )
    def cursor(self):
        try:
            return self.conn.cursor()
        except (AttributeError, MySQLdb.OperationalError):
            self.connect()
            return self.conn.cursor()
    def commit(self):
        return self.conn.commit()
    def close(self):
        return self.conn.close()

dbconn = DBConn()


def ssh_cmd(ip, port, user, passwd, cmd):
    ret = -1
    ssh = pexpect.spawn('ssh -p %s %s@%s %s' % (port, user, ip, cmd))
    try:
        index = ssh.expect(['password:', 'continue connecting (yes/no)?'], timeout = 10)
        if index==0:
            ssh.sendline(passwd)
        elif index==1:
            ssh.sendline('yse\n')
            ssh.expect('password:')
            ssh.sendline(passwd)
        ssh.sendline(cmd)
        r=ssh.read()
        print r
        ret=0
    except pxssh.ExceptionPxssh, e:  
        print "pxssh failed on login."  
        print str(e)   
        ret = -1
    except pexpect.TIMEOUT:
        print "TIMEOUT"
        ssh.close()
        ret = -2
    return ret

def insertData(sql):
    dbconn.connect()
    cur = dbconn.cursor()
#	sql = "insert into user(userid, accout) value('%s', '%s')"%("tutkj90908","1.5")
    try:
        cur.execute(sql)
        dbconn.commit()
    except:
        print "insertData error"
    cur.close()
    dbconn.close()

def selectData(sql):
    dbconn.connect()
    cur = dbconn.cursor()
    results = None
    try:
        cur.execute(sql)
        results = cur.fetchall()
    except:
        print "Error : unable to fetch data "

    cur.close()
    dbconn.close()
    return results

def updateData(sql):
    dbconn.connect()
    cur = dbconn.cursor()
    try:
        cur.execute(sql)
        dbconn.commit()
    except:
        print "update the data error"
    cur.close()
    dbconn.close()

def deleteData(sql):
    dbconn.connect()
    cur = dbconn.cursor()
    try:
        cur.execute(sql)
        dbconn.commit()
    except:
        print "delete data error"
    cur.close()
    dbconn.close()

def line(x):
    now = time.time()
    waiting = now-float(x['ArrivingTime'])
    print int(len(x['IP'].split(';')))
    print int(len(x['IP'].split(';')))*waiting
    return int(len(x['IP'].split(';')))*waiting

def line2(x):
    return int(x['num'])


def test():
    sql = 'select * from TsinghuaCloudMonitor_schedule'
    results = selectData(sql)
    sort=[]

    for i in range(len(results)):
        sort.append(results[i])
    sort.sort(key=line,reverse=True)
    #print 'test'
    for j in range(len(sort)):
        for k in range(len(sort[j]['IP'].split(';'))):
            ipgroup=sort[j]['IP'].split(';')
            namegroup= sort[j]['HostName'].split(';')
            Owner = sort[j]['Owner'].split(';')
            sql2='select Server,count(Target_IP) as num from TsinghuaCloudMonitor_nagios group by Server'
            server_count = selectData(sql2)
            sort2=[]
            for n in range(len(server_count)):
                sort2.append(server_count[n])
                sort2.sort(key=line2)

            sql3= "insert into TsinghuaCloudMonitor_nagios(Server,Target_IP,Target_HostName)value('%s','%s','%s')" % (sort2[0]['Server'],ipgroup[k],namegroup[k])
            insertData(sql3)
            sql4="insert into TsinghuaCloudMonitor_host(IP,HostName,Owner,Info,NagiosServer,HostType,Alias)value('%s','%s','%s','UP','%s','external')" % (ipgroup[k], namegroup[k], Owner[k], sort2[0]['Server'], namegroup[k])
            insertData(sql4)
# <<<<<<< HEAD
# 			#if sort2[0]['Server'] == '01':
# 				#print 'sss'
# 				#ssh_cmd(host1,port,username,passwd,cmd)
# =======
# 			#if sort2[0]['Server'] == '01':
# 				#print 'sss'
# 				#ssh_cmd(host1,port,username,passwd,cmd)
# >>>>>>> lin
            if sort2[0]['Server'] == '01':
                ssh_cmd(host1,port,username,passwd,cmd)
            else:
                ssh_cmd(host2,port,username,passwd,cmd)
        sql5 = "delete from TsinghuaCloudMonitor_schedule where IP = '%s'" % sort[j]['IP']
        deleteData(sql5)
            



#ssh_cmd(host1,port,username,passwd,cmd)
while True:
     test()
     time.sleep(2)
 
   
