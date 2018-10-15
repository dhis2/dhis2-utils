#!/bin/bash

if [ $# -eq 0 ]; then
  echo -e "Usage: $0 <threshold>\n"
  exit 1
fi

LOAD="$(cat /proc/loadavg | awk '{ print $1 }')"
THRESHOLD=$1

echo "Load average: ${LOAD}"
echo "Threshold: ${THRESHOLD}"

if (( $(echo "${LOAD} > ${THRESHOLD}" |bc -l) )); then
  echo "High load detected"
  get_thread_dump
else
  echo "System is stable"
fi
