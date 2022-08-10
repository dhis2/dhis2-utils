#!/bin/bash
#A basic script to stand-up a basic DHIS2 on Ubuntu. 
#The name of the instance. Change as needed.
if [[ $# -lt 1 ]]; then
  echo "Usage: $0 Username"
  exit 1
fi
USERNAME=$1

#Paramaters for specific install
#Name of the database
DB_HOSTNAME="localhost"
#Database port
DB_PORT="5432"
#Path to a database dump in custom format
DUMP_FILE="/tmp/dhis.dump"
#Desired DHIS2 version
VERSION="2.10"
#Desired Tomcat HTTP port
HTTP_PORT=8080
#Desired Tomcat control port
TOMCAT_CONTROL_PORT=8005
DBNAME=$USERNAME
BASE=/home/$USERNAME


while getopts ":dpfchc:" opt; do
	case $opt in
	d)	DB_HOSTNAME=$OPTARG;;
	p)	DB_PORT=$OPTARG;;
	f)  DUMP_FILE=$OPTARG;;
	v)  VERSION=$OPTARG;;
	h)  HTTP_PORT=$OPTARG;;
	c)  TOMCAT_CONTROL_PORT=$OPTARG;;
	\?)	print >&2 "Usage: $0 [-d Database name] directory ..."
		exit 1;;
	esac
done
shift $(($OPTIND-1))

#USER STUFF
#Set the username and password
#Add a user and create some necessary directories
sudo useradd -m -s '/bin/false' $USERNAME
sudo -u $USERNAME tomcat7-instance-create -p $HTTP_PORT -c $TOMCAT_CONTROL_PORT $BASE/tomcat
sudo -u $USERNAME mkdir $BASE/dhis_home
sudo -u $USERNAME sh -c "echo '@reboot $BASE/tomcat/bin/startup.sh' |crontab -u $USERNAME -"
# sudo -u $USERNAME sh -c "echo '03 03 * * * $BASE/backup.sh' |crontab -u $USERNAME -"
#Create a new postgres config and restart the server
PASSWORD=$(makepasswd)
sudo -u postgres psql -c "CREATE ROLE $USERNAME PASSWORD '$PASSWORD' NOSUPERUSER CREATEDB NOCREATEROLE INHERIT LOGIN;"
#Create the database
sudo -u postgres psql -c  "CREATE DATABASE $DBNAME OWNER $USERNAME ENCODING 'UTF-8' TEMPLATE template0;"
sudo -u postgres psql -c  "GRANT ALL ON DATABASE $DBNAME TO $USERNAME;" 
#Uncomment this if you want to restore from a custom dump 
#sudo -u $USERNAME pg_restore --format=custom --ignore-version --no-owner --no-privileges --verbose -U $USERNAME -d $DBNAME $DUMP_FILE

#Download and install DHIS2 
sudo sh -c "sudo -u $USERNAME wget -O $BASE/tomcat/webapps/$USERNAME.war http://dhis2.org/download/releases/$VERSION/dhis.war"
#Create a hibernate.properties file
sudo -u $USERNAME sh -c "echo 'hibernate.dialect = org.hibernate.dialect.PostgreSQLDialect
hibernate.connection.driver_class = org.postgresql.Driver
hibernate.connection.url = jdbc:postgresql://$DB_HOSTNAME:$DB_PORT/$DBNAME
hibernate.connection.username = $USERNAME
hibernate.connection.password = $PASSWORD
hibernate.hbm2ddl.auto = update' >  $BASE/dhis_home/hibernate.properties"
sudo -u $USERNAME chmod 600 $BASE/dhis_home/hibernate.properties


#Create the JAVA_OPTS
#TODO calculate this based on the free memory
sudo sh -c "sudo -u $USERNAME echo -e \"export JAVA_OPTS='-Xmx1024m -Xms512m -XX:MaxPermSize=500m -XX:PermSize=400m'
export DHIS2_HOME='$BASE/dhis_home'
export CATALINA_PID=$BASE/tomcat/work/test-tomcat.pid\" > $BASE/tomcat/bin/setenv.sh"

#Start Tomcat
sudo -u $USERNAME $BASE/tomcat/bin/startup.sh ;
#ToDo Echo where the 
echo "You have successfully installed DHIS2 and it is running at http://localhost:$HTTP_PORT/$USERNAME"
