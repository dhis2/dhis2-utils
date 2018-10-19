#!/bin/bash

#
# Script which can detect high CPU load on a system, and write a series
# of system statistics to log. The first argument specifies the threshold
# for system load based on 'loadavg'. Can typically be scheduled with a 
# cron job to run every minute:
#
# * * * * * /usr/local/bin/monitor_system_load.sh 0.8
#

if [ $# -eq 0 ]; then
  echo -e "Usage: $0 <threshold>\n"
  exit 1
fi

TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
PRETTY_TIMESTAMP=$(date '+%Y/%m/%d %H:%M:%S')
OUTPUT_DIR="/var/log/dhis2-monitoring"
STAT_FILE="${OUTPUT_DIR}/system_stat.log"
LOAD="$(cat /proc/loadavg | awk '{ print $1 }')"
THRESHOLD=$1
CURRENT_USER=$(whoami)

#
# Checks the system load based on 'loadavg' and outputs various system
# log information if above the given threshold.
#
function checkLoad() {
  echo "Load average: ${LOAD}"
  echo "Threshold: ${THRESHOLD}"
  echo "Current user: ${CURRENT_USER}"
  echo ""

  if (( $(echo "${LOAD} > ${THRESHOLD}" |bc -l) )); then
    echo "High load detected on system!"
    echo ""
    createEnvironment
    createSystemStat
    createThreadDump
  else
    echo "System looks OK"
  fi
}

#
# Creates the log directory if it does not already exist.
#
function createEnvironment() {
  sudo mkdir -p ${OUTPUT_DIR}
  sudo chmod 775 ${OUTPUT_DIR}
  sudo chown root:${CURRENT_USER} ${OUTPUT_DIR}
}

#
# Writes a file with system statistics including free, vmstat, loadavg 
# and uptime to the log directory.
#
function createSystemStat() {
  echo "---------------------------------------" >> ${STAT_FILE}
  echo "${PRETTY_TIMESTAMP} - System statistics" >> ${STAT_FILE}
  echo "---------------------------------------" >> ${STAT_FILE}
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
  echo "" >> ${STAT_FILE}
  
  echo "Wrote system stats to: ${STAT_FILE}"
  echo ""
}

#
# Writes thread dumps of the Java process to a compressed archive in the
# log directory.
#
function createThreadDump() {
  JAVA_PID="$(pidof -s java)"
  JAVA_USER="$(ps -o user= -p ${JAVA_PID})"
  FILE_PREFIX="thread_dump"
  TAR_FILE="${FILE_PREFIX}_${TIMESTAMP}.tar.gz"
  
  DUMP_NO=3
  DUMP_PAUSE=8

  echo "Java PID: ${JAVA_PID}, user: ${JAVA_USER}"
  echo "Timestamp: ${TIMESTAMP}"
  echo "Writing ${DUMP_NO} thread dumps with ${DUMP_PAUSE}s in between"
  echo ""

  cd ${OUTPUT_DIR}

  for n in $(seq 1 ${DUMP_NO})
  do
    OUTPUT_FILE="${FILE_PREFIX}_${TIMESTAMP}_${n}.log"
    sudo -u ${JAVA_USER} jstack -l ${JAVA_PID} > ${OUTPUT_FILE}
    echo "Wrote thread dump to: ${OUTPUT_DIR}/${OUTPUT_FILE}"
    sleep ${DUMP_PAUSE}
  done

  tar -czf ${TAR_FILE} ${FILE_PREFIX}_${TIMESTAMP}*.log
  echo ""
  echo "Wrote compressed tar archive to: ${OUTPUT_DIR}/${TAR_FILE}"
  echo ""
    
  cd - > /dev/null
}

checkLoad $1
echo "Done"

