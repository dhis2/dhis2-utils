#!/bin/bash
#Requires curl to be installed on the system. 
#Fill in your username, password, server and directory (i.e "dhis")
USERNAME=
PASSWORD=
SERVER=
DIR=
URL="http://$SERVER/$DIR/dhis-web-maintenance-dataadmin/generateResourceTable.action"

curl --data "organisationUnit=true" -u "$USERNAME:$PASSWORD" $URL
curl --data "dataElementGroupSetStructure=true" -u "$USERNAME:$PASSWORD" $URL
curl --data "indicatorGroupSetStructure=true" -u "$USERNAME:$PASSWORD" $URL
curl --data "organisationUnitGroupSetStructure=true" -u "$USERNAME:$PASSWORD" $URL
curl --data "categoryStructure=true" -u "$USERNAME:$PASSWORD" $URL
curl --data "categoryOptionComboName=true" -u "$USERNAME:$PASSWORD" $URL
curl --data "dataElementStructure=true" -u "$USERNAME:$PASSWORD" $URL
