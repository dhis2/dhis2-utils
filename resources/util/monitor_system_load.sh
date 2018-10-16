#!/bin/bash

if [ $# -eq 0 ]; then
  echo -e "Usage: $0 <threshold>\n"
  exit 1
fi

TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
PRETTY_TIMESTAMP=$(date '+%Y/%m/%d %H:%M:%S')
OUTPUT_DIR="/tmp"
LOAD="$(cat /proc/loadavg | awk '{ print $1 }')"
THRESHOLD=$1

#
# Checks the system load based on 'loadavg' and outputs various system
# log information if above the given threshold.
#
function checkLoad() {
  echo "Load average: ${LOAD}"
  echo "Threshold: ${THRESHOLD}"
  echo ""

  if (( $(echo "${LOAD} > ${THRESHOLD}" |bc -l) )); then
    echo "High load detected on system!"
    echo ""
    createSystemStat
    createNginxLog
    createThreadDump
  else
    echo "System looks OK"
  fi
}

#
# Writes a file with system statistics including free, vmstat, loadavg 
# and uptime to tmp directory.
#
function createSystemStat() {
  STAT_FILE="${OUTPUT_DIR}/system_stat_${TIMESTAMP}.log"
  
  echo "System statistics at ${PRETTY_TIMESTAMP}" > ${STAT_FILE}
  echo "---" >> ${STAT_FILE}
  echo "" >> ${STAT_FILE}
  
  echo "free " >> ${STAT_FILE}
  echo "---" >> ${STAT_FILE}
  free -m >> ${STAT_FILE}
  echo "" >> ${STAT_FILE}
  
  echo "vmstat" >> ${STAT_FILE}
  echo "---" >> ${STAT_FILE}
  vmstat -s >> ${STAT_FILE}
  echo "" >> ${STAT_FILE}
  
  echo "loadavg" >> ${STAT_FILE}
  echo "---" >> ${STAT_FILE}
  cat /proc/loadavg >> ${STAT_FILE}
  echo "" >> ${STAT_FILE}
  
  echo "uptime" >> ${STAT_FILE}
  echo "---" >> ${STAT_FILE}
  uptime  >> ${STAT_FILE}
  echo "" >> ${STAT_FILE}
  
  echo "Wrote system stat file to: ${STAT_FILE}"
  echo ""
}

#
# Writes thread dumps of the Java process to a compressed archive in the
# tmp directory.
#
function createThreadDump() {
  JAVA_PID="$(pidof -s java)"
  JAVA_USER="$(ps -o user= -p ${JAVA_PID})"
  TAR_FILE="thread_dump_${TIMESTAMP}.tar.gz"
  
  DUMP_NO=3
  DUMP_PAUSE=8

  echo "Java PID: ${JAVA_PID}, user: ${JAVA_USER}"
  echo "Timestamp: ${TIMESTAMP}"
  echo "Writing ${DUMP_NO} thread dumps with ${DUMP_PAUSE}s in between"
  echo ""

  cd ${OUTPUT_DIR}

  for n in $(seq 1 ${DUMP_NO})
  do
    OUTPUT_FILE="thread_dump_${TIMESTAMP}_${n}.log"
    sudo -u ${JAVA_USER} jstack -l ${JAVA_PID} > ${OUTPUT_FILE}
    echo "Wrote thread dump to: ${OUTPUT_DIR}/${OUTPUT_FILE}"
    sleep ${DUMP_PAUSE}
  done

  tar -czf ${TAR_FILE} thread_dump_${TIMESTAMP}*.log
  echo ""
  echo "Wrote compressed tar archive to: ${OUTPUT_DIR}/${TAR_FILE}"
  cd - > /dev/null
  echo ""
}

#
# Writes the last lines of the nginx access log file to a compressed
# file in the tmp directory.
#
function createNginxLog() {
  LOG_FILE="/var/log/nginx/access.log"
  OUTPUT_FILE="${OUTPUT_DIR}/nginx_access_${TIMESTAMP}.log.gz"
  tail -n 10000 ${LOG_FILE} | gzip > ${OUTPUT_FILE}
  echo "Wrote nginx access log file to: ${OUTPUT_FILE}"
  echo ""
}

checkLoad $1
echo "Done"

