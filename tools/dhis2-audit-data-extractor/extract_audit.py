import psycopg2
import json
import gzip

DHIS2_CONF_FILE="/home/dhis/config/dhis.conf"
CONN_CONFIG = {
	"host": None,
	"dbname": None,
	"username": None,
	"password": None
}

with open(DHIS2_CONF_FILE) as f:
    lines = f.readlines()


for line in lines:
	split_line = line.split("= ")[1]
	if line.startswith("connection.url"):
		split_url = split_line.split(":")
		if split_url[0] == "jdbc":
			CONN_CONFIG["host"] = "localhost"
			CONN_CONFIG["dbname"] = split_url[2].rstrip() 
	elif line.startswith("connection.username"):
		CONN_CONFIG["username"] = split_line.rstrip()
	elif line.startswith("connection.password"):
		CONN_CONFIG["password"] = split_line.rstrip()

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
