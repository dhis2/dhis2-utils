#!/bin/bash

# Reads all dhis2_user_man_* files found from the current path and writes to file

CONTENT_FILE="help_content.xml"

INCLUDE_FILES=`find . -name "dhis2_user_man_*xml" -type f -printf "%f\n"`

echo "Including the following files:"
echo ${INCLUDE_FILES[@]}

rm -f ${CONTENT_FILE}
touch ${CONTENT_FILE}

echo "<book>" >> ${CONTENT_FILE}

for FILENAME in ${INCLUDE_FILES[@]}
do
  while read -r LINE
  do
    if [[ ${LINE} =~ (<\?xml|<!DOCTYPE|<!ENTITY) ]]; then
      echo "Ignored ${LINE}"
    else
      echo ${LINE} >> ${CONTENT_FILE}
    fi
  done < ${FILENAME}
done

echo "</book>" >> ${CONTENT_FILE}

echo "Done"
