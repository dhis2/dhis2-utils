#!/bin/sh

# Relies on tomcat script to be available
# Does not force fetch of updates

SRC_HOME=~/dev/src/dhis2-core/dhis-2

echo "DHIS 2 source code home: ${SRC_HOME}"

# Build DHIS 2 source

mvn clean install -Pdev -f $SRC_HOME/pom.xml
mvn clean install -Pdev -f $SRC_HOME/dhis-web/pom.xml

echo "Stopping, updating and deploying to tomcat"

tomcat stop
sleep 2
tomcat update
sleep 2
tomcat start
