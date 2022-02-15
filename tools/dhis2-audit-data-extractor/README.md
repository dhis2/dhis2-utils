# DHIS2 Audit Data Extactor
A simple python script to extract audit data from the `audit` table in the  DHIS2 database.

It automatically extracts Postgres connection information from the `/home/dhis/config/dhis.conf` file. If the location is different, please edit the variable `DHIS2_CONF_FILE` in the script.

## Requirements
To use it, you need to install the python package `psycopg2`, which can be installed with:
```
$ pip install psycopg2
```
N.B. You may need to install the package `libpq-dev`. Please refer to your distro's documentation on how to install it.

## Run
As simple as:
```
$ python extract_audit.py
```

You may want to chain the output with `jq` for better results:
```
$ python extract_audit.py | jq -r .
```

## Limitations
As it is, the script has been tested only on a local, all-in-one installation. It hasn't been tested when DHIS2 is deployed in containers.

