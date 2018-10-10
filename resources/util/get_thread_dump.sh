#!/bin/bash

JAVA_PID="$(pidof -s java)"
JAVA_USER="$(ps -o user= -p ${JAVA_PID})"
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
TAR_FILE="thread_dump_${TIMESTAMP}.tar.gz"
OUTPUT_DIR="/tmp"
DUMP_NO=4
DUMP_PAUSE=1

echo "Java PID: ${JAVA_PID}"
echo "Java user: ${JAVA_USER}"
echo "Timestamp: ${TIMESTAMP}"
echo "Writing ${DUMP_NO} thread dumps with ${DUMP_PAUSE}s in between"
echo "---"

cd ${OUTPUT_DIR}

for n in $(seq 1 ${DUMP_NO})
do
  OUTPUT_FILE="thread_dump_${TIMESTAMP}_${n}.txt"
  sudo -u ${JAVA_USER} jstack -l ${JAVA_PID} > ${OUTPUT_FILE}
  echo "Wrote thread dump to: ${OUTPUT_DIR}/${OUTPUT_FILE}"
  sleep ${DUMP_PAUSE}
done

tar -czf ${TAR_FILE} thread_dump_${TIMESTAMP}*.txt
echo "---"
echo "Wrote compressed tar archive to: ${OUTPUT_DIR}/${TAR_FILE}"
cd - > /dev/null
echo "Done!"
