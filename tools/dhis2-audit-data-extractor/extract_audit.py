import psycopg2
import json
import gzip
import configparser
import os
from memory_profiler import profile
import pandas as pd
from sqlalchemy import create_engine

DHIS2_HOME = os.getenv("DHIS2_HOME", "/home/dhis")
DHIS2_CONF_FILE =  "{0}/config/dhis.conf".format(DHIS2_HOME)
CONN_CONFIG = {
    "host": None,
    "dbname": None,
    "username": None,
    "password": None
}
CUR_SIZE = 10


def iter_row(cursor, size=CUR_SIZE):
    while True:
        rows = cursor.fetchmany(size)
        if not rows:
            break
        for row in rows:
            yield row

# Currently, this method doesn't work due to the impossibility to decompress gzip data field.
# More investigation must be done to overcome this issue.
# Additional memory footprint must be assessed.
# @profile
def extract_pandas():
    audit_data = list()
    engine = create_engine("postgresql://{0}:{1}@{2}/{3}".format(
        CONN_CONFIG['username'], CONN_CONFIG['password'], CONN_CONFIG['host'], CONN_CONFIG['dbname']))

    conn = engine.connect().execution_options(
        stream_results=True)

    for chunk_dataframe in pd.read_sql("SELECT * from audit", conn, chunksize=1000):
        df = pd.DataFrame(chunk_dataframe)
        df['createdat'] = df['createdat'].dt.strftime("%Y-%m-%d %H:%M:%S")
        # df['data'] = json.loads(gzip.decompress(df['data']).decode('utf-8'))
        audit_data.append(json.loads(df.to_json(orient="records")))

    return audit_data

# @profile
def extract_pgcopg2():
    audit_data = list()

    conn = psycopg2.connect(
        host=CONN_CONFIG['host'],
        database=CONN_CONFIG['dbname'],
        user=CONN_CONFIG['username'],
        password=CONN_CONFIG['password'])

    cur = conn.cursor()
    cur.execute('SELECT * from audit')

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
            "data": json.loads(gzip.decompress(row[9]).decode('utf-8'))
        }
        audit_data.append(event)

    cur.close()
    return audit_data


def extract_data():
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

    data = extract_pgcopg2()

    #data = extract_pandas()

    print(json.dumps(data))


if __name__ == '__main__':
    extract_data()
