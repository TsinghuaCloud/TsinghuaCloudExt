#! /usr/bin/python
#import pxssh  
#import pexpect
import os
import os.path
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
    except pexpect.EOF:
        print "EOF"
        ssh.close()
        ret = -1
    except pexpect.TIMEOUT:
        print "TIMEOUT"
        ssh.close()
        ret = -2
    return ret 
host='166.111.143.203'
port='22'
username='root'
passwd='tsinghuacloud'
cmd='/usr/local/nagios/etc/Configuration.py'
#ssh_cmd(host,port,username,passwd,cmd)
os.system("touch aaa")
#print aaa
