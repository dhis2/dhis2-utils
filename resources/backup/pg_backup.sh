#!/bin/bash

# The backupdir must be created manually (mkdir pg_backups)
# The backupdir owner must be changed to postgres (chown postgres pg_backups)
# Script must be made executable (chmod 755 pg_backup.sh)
# Script must be invoked by postgres user
# Postgres user must have a home dir (usermod -d /home/postgres postgres) and private/public key pair (ssh-keygen -t rsa)
# Postgres user public key must be uploaded to remote server (if remote copy)

DATE_TIME=`date +%F`
BACKUP_DIR="/var/backups/pg_backups"
DB_NAME="dhis2demo"
BACKUP_FILE="${BACKUP_DIR}/pg-${DB_NAME}-${DATE_TIME}.gz"
REMOTE="true"
REMOTE_DEST="username@backup.com:backup_dir/"

echo "Starting backup of ${DB_NAME} to ${BACKUP_FILE}..."

/usr/bin/pg_dump ${DB_NAME} -U postgres -T aggregated* | gzip > ${BACKUP_FILE}

TIME_INFO=`date '+%T %x'`

echo "Backup file ${BACKUP_FILE} complete at ${TIME_INFO}"
echo "Starting remote copy to ${REMOTE_DEST}..."

if [[ ${REMOTE} == "true" ]]; then
  scp ${BACKUP_FILE} ${REMOTE_DEST}
fi

TIME_INFO=`date '+%T %x'`

echo "Backup file ${BACKUP_FILE} copied to ${REMOTE_DEST} at ${TIME_INFO}"
