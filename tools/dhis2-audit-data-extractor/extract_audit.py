import psycopg2
import json
import gzip
import configparser

DHIS2_CONF_FILE="/home/dhis/config/dhis.conf"
CONN_CONFIG = {
	"host": None,
	"dbname": None,
	"username": None,
	"password": None
}

with open(DHIS2_CONF_FILE, 'r') as f:
    lines = '[conf]\n' + f.read()

config = configparser.ConfigParser()
config.read_string(lines)

conn_url = config.get('conf', 'connection.url')
split_url = conn_url.split(':')
if len(split_url) == 0:
	print("Error: cannot find connection URL string in {0}".format(DHIS2_CONF_FILE))
	exit(1)

db_host = split_url[2].split('/')
if len(db_host) == 1: # in this case string is jdbc:postgresql:database_name
	CONN_CONFIG['host'] = "localhost"
	CONN_CONFIG['dbname'] = db_host[0]
else: # in this case string is jdbc:postgresql://remote.host/database_name
	CONN_CONFIG['host'] = db_host[-2]
	CONN_CONFIG['dbname'] = db_host[-1]

CONN_CONFIG['username'] = config.get('conf', 'connection.username')
CONN_CONFIG['password'] = config.get('conf', 'connection.password')

for k,v in CONN_CONFIG.items():
	if CONN_CONFIG[k] is None:
		print("{0} is None. Parsing error. Check {1}. Quitting".format(k, DHIS2_CONF_FILE))
		exit(1)

conn = psycopg2.connect(
    host=CONN_CONFIG['host'],
    database=CONN_CONFIG['dbname'],
    user=CONN_CONFIG['username'],
    password=CONN_CONFIG['password'])


cur = conn.cursor()

# execute a statement
#print('PostgreSQL database version:')
#cur.execute('SELECT version()')

# display the PostgreSQL database server version
#db_version = cur.fetchone()
#print(db_version)
       
cur.execute('SELECT * from audit')
audit_raw_data = cur.fetchall()

#close the communication with the PostgreSQL
cur.close()  

audit_data = list()
for data in audit_raw_data:
	event = {
		"id": data[0],
		"event": data[1],
		"type": data[2],
		"datetime": data[3].strftime("%Y-%m-%d %H:%M:%S"),
		"createdby": data[4],
		"klass": data[5],
		"uid": data[6],
		"code": data[7],
		"attributes": data[8],
		"data": json.loads(gzip.decompress(data[9]).decode('utf-8'))
	}
	audit_data.append(event)

#print(audit_data)
print(json.dumps(audit_data))
