#!/bin/bash

# Requires cURL

# Set these variables to your environment

DATASET_UID="MoIMRSiNqHR" # UID on server, look up in Web API
BASE_URL="http://localhost:8080" # To DHIS instance
USER="admin" # DHIS username
PWD="district" # DHIS password
FILENAME="form.html"

# Constants, do not change

URL="${BASE_URL}/api/dataSets/${DATASET_UID}/customDataEntryForm"

echo "Using URL: ${URL}"

# PUT to server

`curl -d @${FILENAME} "${URL}" -H "Content-Type:text/html" -u ${USER}:${PWD} -X PUT -v`

echo "Done"

