#!/bin/bash

# Utility script for dropping and restoring databases
# from the dhis2-demo-db Github repository.
#
# Change the `DB_BASE_DIR` variable to match your environment.
#
# Example usage: dhis-restore-db "dev" "2.32"
#

DB_BASE_DIR="/home/lars/dev/src/dhis2-demo-db/sierra-leone"
DB_FILE="dhis2-db-sierra-leone"
TMP_DIR="/tmp"

if [ $# -eq 0 ]; then
  echo -e "Usage: $0 <instance> [<instance>..]\n"
  exit 1
fi

function validate() {
  if [ ! -d $DB_BASE_DIR/$1 ]; then
    echo "Instance $1 does not have the required SQL file database directory."
    exit 1
  fi
}

function run() {
  echo "Restoring database: $1"
  sudo -u postgres dropdb $1
  sudo -u postgres createdb -O dhis $1

  echo "Creating PostGIS extension"
  psql -d $1 -U dhis -c "create extension postgis;"

  cp $DB_BASE_DIR/$1/$DB_FILE.sql.gz ${TMP_DIR}/$DB_FILE-$1.sql.gz
  gunzip -f ${TMP_DIR}/$DB_FILE-$1.sql.gz
  psql -d $1 -U dhis -f ${TMP_DIR}/$DB_FILE-$1.sql
  echo "Restored database: $1"
}

for instance in $@; do
  validate $instance
  run $instance
done
