#!/bin/bash

#This script will generate some statistics on usage of the various report
#types based on access logs. Set the access log path and days according 
#to your environment.

ACCESS_LOG="/usr/local/nginx/logs/access.log"
LOG_DAYS=40

C01=`grep -c "api/reports" ${ACCESS_LOG}`
C02=`grep -c "generateDataSetReport.action" ${ACCESS_LOG}`
C03=`grep -c "getDataCompleteness.action" ${ACCESS_LOG}`
C04=`grep -c "api/documents" ${ACCESS_LOG}`
C05=`grep -c "getOrgUnitDistribution.action" ${ACCESS_LOG}`
C06=`grep -c "exportTable.action" ${ACCESS_LOG}`
C07=`grep -c "getPivotTable.action" ${ACCESS_LOG}`
C08=`grep -c "api/chartValues" ${ACCESS_LOG}`
C09=`grep -c "getGeoJson.action" ${ACCESS_LOG}`

D01=$((C01/LOG_DAYS))
D02=$((C02/LOG_DAYS))
D03=$((C03/LOG_DAYS))
D04=$((C04/LOG_DAYS))
D05=$((C05/LOG_DAYS))
D06=$((C06/LOG_DAYS))
D07=$((C07/LOG_DAYS))
D08=$((C08/LOG_DAYS))
D09=$((C09/LOG_DAYS))

echo "Usage stats: Access last ${LOG_DAYS} days | Average per day"
echo "-----------------------------------------------------------"
echo "Standard report: ${C01} | ${D01}"
echo "Data set report: ${C02} | ${D02}"
echo "Reporting rate summary: ${C03} | ${D03}"
echo "Resources: ${C04} | ${D04}"
echo "Org unit distribution: ${C05} | ${D05}"
echo "Report table: ${C06} | ${D06}"
echo "Web pivot table: ${C07} | ${D07}"
echo "Charts: ${C08} | ${D08}"
echo "Maps: ${C09} | ${D09}"
