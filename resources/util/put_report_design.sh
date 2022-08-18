#!/bin/bash

# Requires cURL

# Set these variables to your environment

REPORT_UID="MoIMRSiNqHR" # UID on server, look up in Web API
REPORT_FILENAME="report.jrxml" # On filesystem in same directory
BASE_URL="http://localhost:8080" # To DHIS instance
USER="admin" # DHIS username
PWD="Admin123" # DHIS password

# Constants, do not change

URL="${BASE_URL}/api/reports/${REPORT_UID}/design"

echo "Using URL: ${URL}"

# PUT to server

`curl -d @${REPORT_FILENAME} "${URL}" -H "Content-Type:application/xml" -u ${USER}:${PWD} -X PUT -v`

echo "Done"
