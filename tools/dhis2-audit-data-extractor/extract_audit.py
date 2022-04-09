from ast import arg
from curses.ascii import NUL
from fileinput import filename
import psycopg2
import json
import gzip
import configparser
import os
#from memory_profiler import profile
#import pandas as pd
#from sqlalchemy import create_engine
import argparse
from datetime import datetime
import csv

DHIS2_HOME = os.getenv("DHIS2_HOME", "/home/dhis")
DHIS2_CONF_FILE =  "{0}/config/dhis.conf".format(DHIS2_HOME)
CONN_CONFIG = {
    "host": None,
    "dbname": None,
    "username": None,
    "password": None
}
CUR_SIZE = 100
AUDITS_NUMBER = 1000
OUTPUT_MODE = "CSV"

def iter_row(cursor, size=CUR_SIZE):
    while True:
        rows = cursor.fetchmany(size)
        if not rows:
            break
        for row in rows:
            yield row

def set_pg_connection():
    with open(DHIS2_CONF_FILE, 'r') as f:
        lines = '[conf]\n' + f.read()

    config = configparser.ConfigParser()
    config.read_string(lines)

    conn_url = config.get('conf', 'connection.url')
    split_url = conn_url.split(':')
    if len(split_url) == 0:
        print("Error: cannot find connection URL string in {0}".format(
            DHIS2_CONF_FILE))
        exit(1)

    db_host = split_url[2].split('/')
    if len(db_host) == 1:  # in this case string is jdbc:postgresql:database_name
        CONN_CONFIG['host'] = "localhost"
        CONN_CONFIG['dbname'] = db_host[0]
    else:  # in this case string is jdbc:postgresql://remote.host/database_name
        CONN_CONFIG['host'] = db_host[-2]
        CONN_CONFIG['dbname'] = db_host[-1]

    CONN_CONFIG['username'] = config.get('conf', 'connection.username')
    CONN_CONFIG['password'] = config.get('conf', 'connection.password')

    for k, v in CONN_CONFIG.items():
        if CONN_CONFIG[k] is None:
            print("{0} is None. Parsing error. Check {1}. Quitting".format(
                k, DHIS2_CONF_FILE))
            exit(1)

def get_audit_number():
    conn = psycopg2.connect(
        host=CONN_CONFIG['host'],
        database=CONN_CONFIG['dbname'],
        user=CONN_CONFIG['username'],
        password=CONN_CONFIG['password'])

    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) from audit')
    data = cur.fetchone()
    cur.close()
    return data[0]

# Currently, this method doesn't work due to the impossibility to decompress gzip data field.
# More investigation must be done to overcome this issue.
# Additional memory footprint must be assessed.
# @profile
# def extract_pandas():
#     audit_data = list()
#     engine = create_engine("postgresql://{0}:{1}@{2}/{3}".format(
#         CONN_CONFIG['username'], CONN_CONFIG['password'], CONN_CONFIG['host'], CONN_CONFIG['dbname']))

#     conn = engine.connect().execution_options(
#         stream_results=True)

#     for chunk_dataframe in pd.read_sql("SELECT * from audit", conn, chunksize=1000):
#         df = pd.DataFrame(chunk_dataframe)
#         df['createdat'] = df['createdat'].dt.strftime("%Y-%m-%d %H:%M:%S")
#         # df['data'] = json.loads(gzip.decompress(df['data']).decode('utf-8'))
#         audit_data.append(json.loads(df.to_json(orient="records")))

#     return audit_data

# @profile
def extract_pgcopg2(format, output_mode, nr_rows, offset):
    audit_data = list()
    format = format.upper()
    output_mode = output_mode.lower()
    current_date = datetime.time(datetime.now())

    conn = psycopg2.connect(
        host=CONN_CONFIG['host'],
        database=CONN_CONFIG['dbname'],
        user=CONN_CONFIG['username'],
        password=CONN_CONFIG['password'])

    cur = conn.cursor()
    cur.execute('SELECT * from audit ORDER BY createdat ASC LIMIT {} OFFSET {}'.format(nr_rows, offset))

    if output_mode == "file":
        filename = "dhis2_audit_extract-{0}.{1}".format(current_date, "csv" if format == "CSV" else "json")
        with open(filename, 'a') as fd:
            writer = csv.DictWriter(fd, fieldnames = ["id", "event", "type", "datetime", "createdby", "klass", "uid", "code", "attributes", "data"])
            if format == "CSV":
                writer.writeheader()

            for row in iter_row(cur):
                event = {
                    "id": row[0],
                    "event": row[1],
                    "type": row[2],
                    "datetime": row[3].strftime("%Y-%m-%d %H:%M:%S"),
                    "createdby": row[4],
                    "klass": row[5],
                    "uid": row[6],
                    "code": row[7],
                    "attributes": row[8],
                    "data": json.loads(gzip.decompress(row[9]).decode('utf-8')) if row[9] else None
                }

                if format == "CSV":
                    writer.writerow(event)
                elif format == "JSON":
                    audit_data.append(event)

            if format == "JSON":
                json.dump(audit_data, fd)
        print("Data saved in {0}".format(filename))
    elif output_mode == "stdout":
        for row in iter_row(cur):
            if format == "CSV":
                event = """{0},{1},{2},{3},{4},{5},{6},{7},'{8}','{9}'""".format(row[0],row[1],row[2],row[3].strftime("%Y-%m-%d %H:%M:%S"),row[4],row[5],row[6],row[7],row[8], json.loads(gzip.decompress(row[9]).decode('utf-8')) if row[9] else None)
            elif format == "JSON":
                event = {
                    "id": row[0],
                    "event": row[1],
                    "type": row[2],
                    "datetime": row[3].strftime("%Y-%m-%d %H:%M:%S"),
                    "createdby": row[4],
                    "klass": row[5],
                    "uid": row[6],
                    "code": row[7],
                    "attributes": row[8],
                    "data": json.loads(gzip.decompress(row[9]).decode('utf-8')) if row[9] else None
                }
            audit_data.append(event)
        if format == "JSON":
            print(json.dumps(audit_data))
        else:
            for row in audit_data:
                print(row)

    cur.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', nargs='?', choices=['extract', 'enum'] )
    parser.add_argument('-e', '--entries', type=int, help="Number of rows to pull. Default 1000", default=1000)
    parser.add_argument('-m', '--mode', type=str, choices=['file', 'stdout'], default="file")
    parser.add_argument('-f', '--format', type=str, choices=['CSV', 'JSON'], default="CSV")
    parser.add_argument('-s', '--skip', type=int, help="Number of rows to skip", default=0)

    args = parser.parse_args()

    set_pg_connection()
    if args.command:
        if args.command.lower() == "extract":
            extract_pgcopg2(args.format, args.mode, args.entries, args.skip)
            #data = extract_pandas()
        elif args.command.lower() == "enum":
            print("Audit table contains {} entries".format(get_audit_number()))
    else:
        parser.print_help()
