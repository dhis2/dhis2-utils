# DHIS2 Audit Data Extactor
A simple python script to extract audit data from the `audit` table in the  DHIS2 database.

It automatically extracts Postgres connection information from the config file `config/dhis.conf` via the environment variable `DHIS2_HOME`. If the location is different, please set the environment variable `DHIS2_HOME` as appropriate. Default is `/home/dhis/config/dhis.conf`.

The script uses python library psycopg2, although some tests have been done with pandas. Code is left here as a reference for future development.

## Version 1.1
- Basic logging thanks to `--verbose` and `--severity` (`low`, `medium` and `high`).
- Option to specify a DHIS2 config file from command line.
- Support for parsing more different database connection URL strings.

## Version 1.0
- Automatically connects to DHIS2 postgres database by parsing DHIS2 config file.
- List and extract rows from audit table.
- Output in CSV (default) and JSON.
- Automatically saves to file.
- Option to output to stdout.
- Option to specify a file for saving output.
- Option to select the number of events to extract.
- Option to skip rows.

## Requirements
Install requirements:
```
$ pip install -r requirements.txt
```
N.B. You may need to install the package `libpq-dev`. Please refer to your distro's documentation on how to install it.

## Run
```
~/dhis2-utils/tools/dhis2-audit-data-extractor$ python extract_audit.py
usage: extract_audit.py [-h] [-c CONFIG] [-e ENTRIES] [-m {file,stdout}] [-f {CSV,JSON}] [-s SKIP] [-o OUTPUT] [-V] [-v] [-sv SEVERITY] [{extract,enum}]


positional arguments:
  {extract,enum}

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Select a DHIS2 config file
  -e ENTRIES, --entries ENTRIES
                        Number of rows to pull. Default 1000
  -m {file,stdout}, --mode {file,stdout}
  -f {CSV,JSON}, --format {CSV,JSON}
  -s SKIP, --skip SKIP  Number of rows to skip
  -o OUTPUT, --output OUTPUT
                        Output file
  -V, --version         Print version and exit
  -v, --verbose         Turn on verbose logging with default severity of low
  -sv SEVERITY, --severity SEVERITY
                        Set the severity for logging. Default to low. Verbose flag must also be set

Version 1.1
~/dhis2-utils/tools/dhis2-audit-data-extractor$
```

You can enumerate how many events (=rows) there are in the table:
```
~/dhis2-utils/tools/dhis2-audit-data-extractor$ python extract_audit.py enum
Audit table contains 612 entries
~/dhis2-utils/tools/dhis2-audit-data-extractor$
```

By default the script saves the data to a file (`-m file`) automatically created in the current folder. Format is CSV (`-f CVS`).

```
$ python extract_audit.py extract
```

With large tables, you may want to extract only a subset of events. You can do it by settin the `--entries` and `--skip` paramenters. The command below pulls 100 events starting from row 10:
```
$ python extract_audit.py extract -e 100 -s 10
```

You can append the data to an already existing file the following way:
```
$ python extract_audit.py extract -o results.csv -e 10
$ python extract_audit.py extract -o results.csv -e 10 -s 10
```

Bear in mind that while selecting the JSON mode, a JSON object will be appended as a standalone entity, thus not merged into one single JSON.
```
$ python extract_audit.py extract -f JSON -o results.json -e 10
Data saved in results.json
$ cat results.json | jq length
10
$ python extract_audit.py extract -f JSON -o results.json -e 10 -s 10
Data saved in results.json
$ cat results.json | jq length
10
10
$
```

## Limitations
As it is, the script has been tested only on a local, all-in-one installation. It hasn't been tested when DHIS2 is deployed in containers.

