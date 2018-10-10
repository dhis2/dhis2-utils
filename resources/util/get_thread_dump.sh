#!/bin/bash

JAVA_PID="$(pidof java)"
JAVA_USER="$(ps -o user= -p ${JAVA_PID})"
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
TARFILE="thread_dump_${TIMESTAMP}.tar.gz"
OUTPUT_DIR="/tmp"

echo "Java PID: ${JAVA_PID}"
echo "Java user: ${JAVA_USER}"
echo "Timestamp: ${TIMESTAMP}"

cd ${OUTPUT_DIR}

for n in {1..4}
do
  OUTPUT_FILE="thread_dump_${TIMESTAMP}_${n}.txt"
  sudo -u ${JAVA_USER} jstack -l ${JAVA_PID} > ${OUTPUT_FILE}
  echo "Output file: ${OUTPUT_DIR}/${OUTPUT_FILE}"
  sleep 1
done
 
tar -cvzf ${TARFILE} thread_dump_${TIMESTAMP}*.txt

echo "Wrote tar archive: ${OUTPUT_DIR}/${TARFILE}"

cd -

echo "Done"
