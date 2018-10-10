#!/bin/bash

JAVA_PID="$(pidof java)"
JAVA_USER="$(ps -o user= -p ${JAVA_PID})"
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
TARFILE="thread_dump_${TIMESTAMP}.tar.gz"
OUTPUT_DIR="/tmp"
DUMP_NO=4
DUMP_PAUSE=10

echo "Java PID: ${JAVA_PID}"
echo "Java user: ${JAVA_USER}"
echo "Timestamp: ${TIMESTAMP}"
echo "Thread dump pause: ${DUMP_PAUSE}s"
echo "---"

cd ${OUTPUT_DIR}

for n in {1..4}
do
  OUTPUT_FILE="thread_dump_${TIMESTAMP}_${n}.txt"
  sudo -u ${JAVA_USER} jstack -l ${JAVA_PID} > ${OUTPUT_FILE}
  echo "Wrote thread dump to: ${OUTPUT_DIR}/${OUTPUT_FILE}"
  sleep ${DUMP_PAUSE}
done

tar -czf ${TARFILE} thread_dump_${TIMESTAMP}*.txt
echo "Wrote compressed tar archive to: ${OUTPUT_DIR}/${TARFILE}"
cd - > /dev/null
echo "Done"
