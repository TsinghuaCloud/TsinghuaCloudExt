#/bin/bash
apt-get update 
apt-get install -y apache2 
apt-get install -y libapache2-mod-php5 
apt-get install -y build-essential 
apt-get install -y php5-gd 
apt-get install -y libgd2-xpm-dev 
apt-get install -y libgd2-xpm 
apt-get install -y openssl 
apt-get install -y make 
apt-get install -y libssl-dev
useradd nagios -s /sbin/nologin && 
tar xvf nagios-plugins-2.0.tar.gz 
cd nagios-plugins-2.0
./configure --prefix=/usr/local/nagios 
make 
make install 
chown -R nagios:nagios /usr/local/nagios 
chown -R nagios:nagios /usr/local/nagios/libexec 
cd .. 
tar zxvf nrpe-2.14.tar.gz 
cd nrpe-2.14 
./configure --with-ssl=/usr/bin/openssl --with-ssl-lib=/usr/lib/x86_64-linux-gnu
make all 
make install-plugin 
make install-daemon 
make install-daemon-config 
sed -i 's/^allowed_hosts=127.0.0.1/&,166.111.143.203/' /usr/local/nagios/etc/nrpe.cfg 
/usr/local/nagios/bin/nrpe -c /usr/local/nagios/etc/nrpe.cfg -d

