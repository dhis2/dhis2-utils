#!/bin/bash
#These two variables must be modified to suit your purposes
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 Username"
  exit 1
fi
USERNAME=$1
#TODO paramaterize this
PG_VERSION="9.2"
VHOST="foo.com"
#SERVER STUFF 
#Update first
sudo apt-get -y update
sudo apt-get -y upgrade

#Install postgres
#Installs Postgres 9.2 from a custom repository. Adjust as needed
sudo apt-get -y install python-software-properties
sudo add-apt-repository -y ppa:pitti/postgresql
sudo apt-get -y update
sudo apt-get -y install postgresql-$PG_VERSION tomcat7-user libtcnative-1 nginx makepasswd bc ufw ttf-dejavu ttf-liberation

#KERNEL STUFF
#Make some changes to the kernel params
#TODO Ask the user if they want to do this.
MEMTOTAL=$(grep MemTotal /proc/meminfo | awk '{print $2}')
MEMFREE=$(grep MemFree /proc/meminfo | awk '{print $2}')
SHMAX=$(bc -l <<< "scale = 0;($MEMTOTAL*1024/12)")
RMEM_MAX=$(bc -l <<< "scale = 0;$SHMAX/128")
PG_VERSION=$(sudo -u postgres psql -t -c  "SELECT substring(version() from '[8-9]\.[0-9]');" | sed 's/^\s//g')


sudo sh -c "echo '
kernel.shmmax = $SHMAX
net.core.rmem_max = $RMEM_MAX
net.core.wmem_max = $RMEM_MAX' >> /etc/sysctl.conf" 
sudo sysctl -p


#Backup the Postgres configuration file
sudo cp /etc/postgresql/$PG_VERSION/main/postgresql.conf /etc/postgresql/$PG_VERSION/main/postgresql.conf.bak

#Basic Postgres Optimization 
#TODO.Need to ask for user input here whether they really want to do this.
sudo sh -c "sudo -u postgres echo -e \"data_directory = '/var/lib/postgresql/$PG_VERSION/main'\n         
hba_file = '/etc/postgresql/$PG_VERSION/main/pg_hba.conf'\n       
ident_file = '/etc/postgresql/$PG_VERSION/main/pg_ident.conf'\n  
external_pid_file = '/var/run/postgresql/$PG_VERSION-main.pid'\n         
port = 5432\n                            
max_connections = 100\n                  
unix_socket_directory = '/var/run/postgresql'\n         
ssl = false\n                             
shared_buffers = $(bc -l <<< "scale = 0;($MEMTOTAL/24576)")MB\n                  
log_line_prefix = '%t '\n                 
datestyle = 'iso, mdy'\n
lc_messages = 'en_US.UTF-8'\n                     
lc_monetary = 'en_US.UTF-8'\n                     
lc_numeric = 'en_US.UTF-8'\n                     
lc_time = 'en_US.UTF-8'\n                        
default_text_search_config = 'pg_catalog.english'\n
effective_cache_size = $(bc -l <<< "scale = 0;($MEMTOTAL*0.3/1024)")MB\n
checkpoint_segments = 32\n
checkpoint_completion_target = 0.8\n
wal_buffers = 4MB\n
synchronous_commit = off\n
wal_writer_delay = 10000ms\n\"  > /etc/postgresql/$PG_VERSION/main/postgresql.conf"

#NGINX Configuration
#Nginx configuration
sudo cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak
#Main ngnix config
sudo sh -c "sudo -u root echo -e \"user www-data;
worker_processes  4;
error_log  /var/log/nginx/error.log;
pid        /var/run/nginx.pid;
events {
     worker_connections  1024;
     use epoll;
  }
 
  http {
    include       /etc/nginx/mime.types;
    access_log /var/log/nginx/access.log;
    sendfile        on;
    keepalive_timeout  65;
    tcp_nodelay        on;
    server_names_hash_bucket_size 64;
    gzip                on;
    gzip_comp_level     1;
    gzip_disable        msie6;
    gzip_proxied        any;
    gzip_types          text/plain text/css application/x-javascript text/xml application/xml application/rss+xml text/javascript;
    proxy_cache_path  /var/cache/nginx keys_zone=dhis:250m inactive=1d;
    proxy_redirect off;
    # Cache different return codes for different lengths of time
    proxy_cache_valid 200 302  6h;
    proxy_cache_valid 404      1m;
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
  }\n\" > /etc/nginx/nginx.conf"

sudo sh -c "sudo -u root echo -e \"server {
listen *:80;
server_name _;
client_max_body_size 15M;
client_body_buffer_size 128k;
access_log  /var/log/nginx/$USERNAME.access.log;
location / {
    root   /var/www/nginx-default;
    index  index.html index.htm;
        }
 # Serve static content
  location ~ ^/$USERNAME/.*(\.js$|\.css$|\.gif$|\.woff$|\.ttf$|\.eot$|\.html$|images/|icons/|dhis-web-commons/.*\.png$) {
    root     /home/$USERNAME/tomcat/webapps/;
    add_header  Cache-Control  public;
    expires  7d;
  }

location /dhis/ {
    proxy_pass http://localhost:8080/dhis/;
    proxy_redirect off;
    proxy_set_header            Host \044http_host;
    proxy_set_header            X-Real-IP \044remote_addr;
    proxy_set_header            X-Forwarded-For \044proxy_add_x_forwarded_for;
    proxy_cache       $USERNAME;
    expires +24h;
  }
rewrite ^/$ /$USERNAME/ permanent;
}\" > /etc/nginx/sites-available/$USERNAME"
sudo ln -s /etc/nginx/sites-available/$USERNAME /etc/nginx/sites-enabled/$USERNAME
sudo /etc/init.d/nginx restart

#Restart postgres
sudo /etc/init.d/postgresql restart $PG_VERSION
#Restart Tomcat
sudo -u $USERNAME /home/$USERNAME/tomcat/bin/shutdown.sh
sudo -u $USERNAME /home/$USERNAME/tomcat/bin/startup.sh

echo "Please remember to configure your firewall!"
