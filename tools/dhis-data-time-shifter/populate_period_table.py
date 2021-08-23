import json
import chardet
from dhis2 import Api, RequestException, setup_logger, logger, is_valid_uid, generate_uid
from re import match, findall, compile, search, sub
from datetime import date, datetime, timedelta


# Date in format yyyy-mm-dd
def get_periods(frequency, start_date, end_date):
    # datetime.strptime(startDate, "%Y%m%d").strftime("%Y-%m-%d")
    dt_start = datetime.strptime(start_date, "%Y-%m-%d")
    dt_end = datetime.strptime(end_date, "%Y-%m-%d")
    periods = list()

    if dt_start < dt_end:
        if frequency.lower() == 'daily':  # yyyyMMdd
            for single_date in (dt_start + timedelta(n) for n in range((dt_end - dt_start).days + 1)):
                periods.append(single_date.strftime("%Y%m%d"))

        elif frequency.lower() == 'weekly':  # yyyyWn
            single_date = dt_start
            while single_date <= dt_end:
                periods.append(str(single_date.year) + 'W' + str(single_date.isocalendar()[1]))
                single_date = single_date + timedelta(7)  # 7 days, a week

        elif frequency.lower() == 'monthly':  # yyyyMM
            start_month = dt_start.month
            end_month = dt_end.month
            start_year = dt_start.year
            end_year = dt_end.year
            for year in range(start_year, (end_year + 1)):
                last_month = 12
                first_month = 1
                if year == start_year:
                    first_month = start_month
                if year == end_year:
                    last_month = end_month
                for month in range(first_month, (last_month + 1)):
                    periods.append(str(year) + str(month).zfill(2))

        elif frequency.lower() == 'quarterly':  # yyyyQn
            start_quarter = (dt_start.month - 1) // 3 + 1
            end_quarter = (dt_end.month - 1) // 3 + 1
            start_year = dt_start.year
            end_year = dt_end.year
            for year in range(start_year, (end_year + 1)):
                last_quarter = 4
                first_quarter = 1
                if year == start_year:
                    first_quarter = start_quarter
                if year == end_year:
                    last_quarter = end_quarter
                for quarter in range(first_quarter, (last_quarter + 1)):
                    periods.append(str(year) + 'Q' + str(quarter))

        elif frequency.lower() == 'yearly':  # yyyy
            start_year = dt_start.year
            end_year = dt_end.year
            for year in range(start_year, (end_year + 1)):
                periods.append(str(year))
        else:
            logger.error("Period type = '" + frequency + "' not supported")
            exit(1)
    else:
        logger.error("Start date = '" + start_date + "' is after end date = '" + end_date + "'")
        exit(1)

    return periods

import sys
if len(sys.argv) < 4:
    print('Please specify at least frequency (Daily, Weekly, Monthly, Quarterly, Yearly) as well as start_date and end_date as YYYY-MM-DD')
    exit()

frequency = sys.argv[1]
start_date = sys.argv[2]
end_date = sys.argv[3]
if len(sys.argv) > 4:
    instance = sys.argv[4]
else:
    instance = None

credentials_file = 'auth.json'

try:
    f = open(credentials_file)
except IOError:
    print("Please provide file auth.json with credentials for DHIS2 server")
    exit(1)
else:
    with open(credentials_file, 'r') as json_file:
        credentials = json.load(json_file)
    if instance is not None:
        api = Api(instance, credentials['dhis']['username'], credentials['dhis']['password'])
    else:
        api = Api.from_auth_file(credentials_file)

de_uid = generate_uid()

dummy_data_de = {
  "id": de_uid,
  "name": "Dummy data placeholder",
  "shortName": "Dummy data placeholder",
  "aggregationType": "NONE",
  "domainType": "AGGREGATE",
  "publicAccess": "--------",
  "externalAccess": False,
  "valueType": "NUMBER",
  "zeroIsSignificant": False,
  "favorite": False,
  "optionSetValue": False,
}

# First, create the data element
try:
    response = api.post('metadata', params={'mergeMode': 'REPLACE', 'importStrategy': 'CREATE_AND_UPDATE'},
                        json={'dataElements':[dummy_data_de]})
except RequestException as e:
    # Print errors returned from DHIS2
    logger.error("POST failed with error " + str(e))
    exit()
else:
    print('Data element ' + de_uid + ' created')

# Get OU level 1
try:
    ou = api.get('organisationUnits', params={'fields': 'id,name', 'filter': 'level:eq:1'}).json()['organisationUnits']
except RequestException as e:
    # Print errors returned from DHIS2
    logger.error("GET ou failed with error " + str(e))
    exit()
else:
    print('Using root OU ' + ou[0]['name'])
    ou_uid = ou[0]['id']

# Get periods
dataValueSets = list()
for period in get_periods(frequency, start_date, end_date):
    print("Creating dummy data for period " + period)
    dataValueSets.append({"dataElement": dummy_data_de['id'], "value": 0, "orgUnit": ou_uid, "period": period})

print('Posting values')
try:
    response = api.post('dataValueSets', params={'mergeMode': 'REPLACE', 'importStrategy': 'CREATE_AND_UPDATE'},
                        json={"dataValues":dataValueSets})
except RequestException as e:
    # Print errors returned from DHIS2
    logger.error("POST failed with error " + str(e))
    exit()
else:
    print('Values created')

print('Deleting values')
try:
    response = api.post('dataValueSets', params={'mergeMode': 'REPLACE', 'importStrategy': 'DELETE'},
                        json={"dataValues":dataValueSets})
except RequestException as e:
    # Print errors returned from DHIS2
    logger.error("POST failed with error " + str(e))
    exit()
else:
    print('Values deleted')

print('Deleting DE ' + de_uid)
try:
    response = api.delete('dataElements/' + de_uid)
except RequestException as e:
    # Print errors returned from DHIS2
    logger.error("DELETE failed with error " + str(e))
    exit()
else:
    print('DE deleted')
