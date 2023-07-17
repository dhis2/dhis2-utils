# make sure you have dhis2.py installed, otherwise run "pip3 install dhis2.py"
from dhis2 import Api, RequestException, is_valid_uid, load_csv
import json
import re
import logzero
from logzero import logger
from datetime import date, datetime, timedelta
from faker import Faker
from random import randrange, random, choice, uniform, seed, sample
import sys
import pandas as pd
from numpy import isnan

# setup the logger
log_file = "./dummyDataAggregated.log"
logzero.logfile(log_file)

def post_to_server(jsonObject, apiObject='metadata', strategy='CREATE_AND_UPDATE'):
    try:
        response = api_source.post(apiObject, params={'mergeMode': 'REPLACE', 'importStrategy': strategy},
                                   json=jsonObject)

    except RequestException as e:
        # Print errors returned from DHIS2
        logger.error("metadata update failed with error " + str(e))
    else:
        if response is None:
            logger.error("Error in response from server")
            return
        text = json.loads(response.text)
        # print(text)
        if text['status'] == 'ERROR':
            logger.error(text)
        # errorCode = errorReport['errorCode']
        else:
            if apiObject == 'metadata':
                logger.info("metadata imported :" + text['status'] + " " + json.dumps(text['stats']))
            else:
                logger.info("data imported :" + text['status'] + " " + json.dumps(text['importCount']))
                if text['status'] == 'WARNING': logger.warning(text)


def isDateFormat(input):
    try:
        datetime.strptime(input, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def reindex(json_object, key):
    new_json = dict()
    for elem in json_object:
        key_value = elem[key]
        # elem.pop(key)
        new_json[key_value] = elem
    return new_json


def extract_json_element_as_list(jsonArray, elem):
    result = list()
    for jsonObj in jsonArray:
        if elem in jsonObj:
            result.append(jsonObj[elem])
    return result


def value_type_is_numeric(value_type):
    numeric_value_types = ['INTEGER_POSITIVE', 'AGE', 'INTEGER_ZERO_OR_POSITIVE', 'INTEGER', 'INTEGER_NEGATIVE',
                           'NUMBER']
    return value_type in numeric_value_types


def convert_value(value, value_type):
    if isnan(value):
        return None
    else:
        if value_type == 'NUMBER':
            return float(value)
        else:
            return int(value)


def get_min_max_from_df(df, value_type, de_uid, coc_uid=None):
    min_value = max_value = None
    if value_type_is_numeric(value_type):
        df_filtered = None
        if coc_uid is not None:
            df_filtered = df[(df['DE UID'] == de_uid) & (df['COC UID'] == coc_uid)]
        else:
            df_filtered = df[df['DE UID'] == de_uid]

        if df_filtered.shape[0] == 1:
            min_value = convert_value(df_filtered['min'].values[0], value_type)
            max_value = convert_value(df_filtered['max'].values[0], value_type)

        # else:
        #     logger.warning("Could not find min/max values for DE = " + de_uid + " COC = " + str(coc_uid))

        return min_value, max_value

# random.random()
# random.uniform(a, b)
# random.triangular(low, high, mode)
# random.betavariate(alpha, beta)
# random.expovariate(lambd)
# random.gammavariate(alpha, beta)
# random.gauss(mu, sigma)
# random.lognormvariate(mu, sigma)
# random.normalvariate(mu, sigma)
# random.vonmisesvariate(mu, kappa)
# random.paretovariate(alpha)
# random.weibullvariate(alpha, beta)

def generate_dummy_numeric_value(value_type, min_value, max_value):
    value = 0
    if min_value == max_value == 0:
        return value

    if min_value is None: min_value = -100
    if max_value is None: max_value = 100
    if value_type == "INTEGER_POSITIVE":
        if min_value <= 0:
            min_value = 1
        value = randrange(min_value, max_value)

    elif value_type == "INTEGER_ZERO_OR_POSITIVE":
        if min_value < 0:
            min_value = 0
        value = randrange(min_value, max_value)

    elif value_type == "INTEGER_NEGATIVE":
        if max_value >= 0:
            max_value = -1
        value = randrange(min_value, max_value)

    elif value_type == "INTEGER":
        value = randrange(min_value, max_value)

    elif value_type == "NUMBER":
        value = round(uniform(min_value, max_value), 2)
    return value

def generate_dummy_value(dummy_data_params):
    # COORDINATE
    # INTEGER_POSITIVE
    # AGE
    # FILE_RESOURCE
    # BOOLEAN
    # TEXT
    # ORGANISATION_UNIT
    # IMAGE
    # LONG_TEXT
    # INTEGER_ZERO_OR_POSITIVE
    # INTEGER
    # DATE
    # TRUE_ONLY
    # TIME
    # PERCENTAGE
    # INTEGER_NEGATIVE
    # NUMBER

    faker = Faker()
    value = None
    value_type = dummy_data_params['value_type']
    min_value = dummy_data_params['min_value']
    max_value = dummy_data_params['max_value']
    options = dummy_data_params['options']

    if options is not None:
        value = choice(options)

    elif value_type_is_numeric(value_type):
        value = generate_dummy_numeric_value(value_type, min_value, max_value)

    elif value_type == "BOOLEAN":
        value = choice(['true', 'false'])

    elif value_type == "TRUE_ONLY":
        # If present, it should be True, although if the user has unchecked it, it will be false
        value = choice(['true', None])

    elif value_type == "DATE":
        if min_value is None: min_value = date(year=2015, month=1, day=1)
        if max_value is None: max_value = datetime.today()
        value = faker.date_between(start_date=min_value, end_date=max_value).strftime("%Y-%m-%d")

    elif value_type == "TIME":
        value = faker.time()[0:5] # To get HH:MM and remove SS

    elif value_type == "TEXT":
        value = faker.text()[0:56]

    elif value_type == "LONG_TEXT":
        value = faker.text()

    else:
        value = 0  # We should not get here


    return value


def get_org_units(selection_type, value, random_size = None):

    global api_source

    org_units = list()
    if selection_type == 'uid':
        # Hardcoded list of OU UIDs separated by commas
        org_units = value.split(',')
        for ou_uid in org_units:
            if not is_valid_uid(ou_uid):
                logger.error('OU uid provided ' + ou_uid + ' is not valid')
                exit(1)
    else:
        ou_filter = ""
        if selection_type == 'uid_children':
            if not is_valid_uid(value):
                logger.error('OU uid provided for parent ' + value + ' is not valid')
                exit(1)
            ou_filter = "parent.id:in:[" + value + "]"  # To verify
        elif selection_type == 'name':
            ou_filter = "name:in:[" + value + "]"  # To verify
        elif selection_type == 'ilike':
            ou_filter = "name:ilike:" + value  # To verify
        elif selection_type == 'code':
            ou_filter = "code:in:[" + value + "]"
        elif selection_type == 'level':
            if value.isnumeric() and 0 < int(value):
                ou_filter = "level:in:[" + value + "]"
            else:
                logger.error('OU level to use must be integer positive, ' + value + ' is not valid')
                exit(1)
        else:
            logger.error("Unknown parameter for OU selection: " + selection_type)
            exit(1)

        OUs = api_source.get('organisationUnits',
                             params={"paging": "false", "fields": "id,name",
                                     "filter": ou_filter}).json()['organisationUnits']

        logger.warning("Found " + str(len(OUs)) + " OUs")
        org_units = extract_json_element_as_list(OUs, 'id')
        if random_size is not None and len(org_units) > random_size:
            logger.warning("Extracting random sample of " + str(random_size) + " size")
            org_units = sample(org_units, random_size)

    return org_units


def is_ou_assigned_to_ds(ou_uid, dataset):
    found = False

    if 'organisationUnits' in dataset:
        for ou in dataset['organisationUnits']:
            if ou['id'] == ou_uid:
                found = True
                break

    return found


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


def main():
    import argparse
    global api_source

    my_parser = argparse.ArgumentParser(prog='dummy_data_agg',
                                        description='Create dummy data for aggregated datasets',
                                        epilog="example1"
                                               "\nexample2",
                                        formatter_class=argparse.RawDescriptionHelpFormatter)
    my_parser.add_argument('Dataset', metavar='dataset_param', type=str,
                           help='the uid of the dataset to use or a string to filter datasets')
    my_parser.add_argument('-sd', '--start_date', action="store", dest="start_date", type=str,
                           help='start date for the period to use to generate data (default is today - 1 year)')
    my_parser.add_argument('-ptf', '--period_type_filter', action="store", dest="period_type_filter", type=str,
                           help='only applicable when having multiple datasets: d, w, m, y')
    my_parser.add_argument('-ed', '--end_date', action="store", dest="end_date", type=str,
                           help='end date for the period to use to generate data (default is today)')
    my_parser.add_argument('-ous', '--org_unit_selection', action="store", metavar=('type', 'value'), nargs=2,
                           help='Provide a type of org unit selection from [uid,uid_children,name,code,level] and the value to use'
                                'Eg: --ous uid QXtjg5dh34A')
    # Parameters should be 0 or 1
    my_parser.add_argument('-cf', '--create_flat_file', action="store", metavar='file_name', const='xxx', nargs='?',
                           help='Create spreadsheet for min/max values'
                                'Eg: --create_flat_file=my_file.csv')
    my_parser.add_argument('-uf', '--use_flat_file', action="store", metavar='file_name', type=str,
                           help='Use spreadsheet for min/max values'
                                'Eg: --use_flat_file=my_file.csv')
    my_parser.add_argument('-i', '--instance', action="store", dest="instance", type=str,
                           help='instance to use for dummy data injection (robot account is required!) - default is the URL in auth.json')
    my_parser.add_argument('-ours', '--ous_random_size', action="store", dest="ous_random_size", type=str,
                           help='From all OUs selected from ous command, takes a random sample of ous_random_size')

    args = my_parser.parse_args()


    if args.use_flat_file is not None:
        filename = args.use_flat_file
        print(filename)
        logger.info("Reading " + filename + " for min/max value")
        df_min_max = pd.read_csv('./' + filename, sep=None, engine='python')

    credentials_file = 'auth.json'

    try:
        f = open(credentials_file)
    except IOError:
        print("Please provide file auth.json with credentials for DHIS2 server")
        exit(1)
    else:
        with open(credentials_file, 'r') as json_file:
            credentials = json.load(json_file)
        if args.instance is not None:
            #api_source = Api(args.instance, 'admin', 'district')
            api_source = Api(args.instance, credentials['dhis']['username'], credentials['dhis']['password'])
        else:
            api_source = Api.from_auth_file(credentials_file)

    logger.warning("Server source running DHIS2 version {} revision {}"
                   .format(api_source.version, api_source.revision))

    #WHAT
    dsParam = args.Dataset
    # WHERE
    ouUIDs = list()
    #WHEN
    start_date = ""
    end_date = ""
    periods = list()

    # Assign values from parameters provided if applicable
    if args.create_flat_file is None: # If we are creating a flat file it does not matter if not provided
        if args.org_unit_selection is None:
            print('Please provide a value for org_unit_selection to create the dummy data')
        else:
            if len(args.org_unit_selection) >= 1:
                if args.ous_random_size is not None:
                    ouUIDs = get_org_units(args.org_unit_selection[0], args.org_unit_selection[1], int(args.ous_random_size))
                else:
                    ouUIDs = get_org_units(args.org_unit_selection[0], args.org_unit_selection[1])
                if len(ouUIDs) == 0:
                    print('The OU selection ' + args.org_unit_selection[0] + ' '
                          + args.org_unit_selection[1] + ' returned no result')
                    exit(1)

        if args.start_date is None:
            start_date = (date.today() - timedelta(days=365)).strftime("%Y-%m-%d")
        else:
            start_date = args.start_date
            if not isDateFormat(start_date):
                print('Start date provided ' + start_date + ' has a wrong format')
                exit(1)
        if args.end_date is None:
            end_date = (date.today()).strftime("%Y-%m-%d")
        else:
            end_date = args.end_date
            if not isDateFormat(end_date):
                print('End date provided ' + end_date + ' has a wrong format')
                exit(1)

    periods = list()

    if args.create_flat_file is not None:
        df_min_max = pd.DataFrame({}, columns=['DE UID', 'COC UID', 'DE Name', 'COC Name', 'valueType', 'min', 'max'])
    else:
        df_min_max = None

    if args.use_flat_file is not None:
        filename = args.use_flat_file
        logger.info("Reading " + filename + " for min/max value")
        df_min_max = pd.read_csv(filename, sep=None, engine='python')


    CC = api_source.get('categoryCombos', params={"paging": "false", "fields": "id,name,categoryOptionCombos"}).json()[
        'categoryCombos']
    CC = reindex(CC, 'id')
    defaultCC = ''
    for catcomboUID in CC:
        if CC[catcomboUID]['name'] == 'default':
            defaultCC = catcomboUID
            break
    if defaultCC == '':
        logger.warning('Could not find default Category Combo')

    COC = api_source.get('categoryOptionCombos',
                         params={"paging": "false", "fields": "id,name,code"}).json()['categoryOptionCombos']
    COC = reindex(COC, 'id')

    DE = api_source.get('dataElements',
                        params={"paging": "false", "fields": "id,name,code,categoryCombo,aggregationType,valueType,optionSet"}).json()[
        'dataElements']
    DE = reindex(DE, 'id')

    # Check for optionSets in the DE
    optionSetUIDs = list()
    for de in DE:
        if 'optionSet' in de:
            optionSetUIDs.append(de['optionSet']['id'])
    if len(optionSetUIDs) > 0:
        options = api_source.get('options',
                        params={"paging": "false", "fields": "id,name,code",
                                "filter":"optionSet.id:eq:"+','.join(optionSetUIDs)}).json()['options']

    de_numeric_types = ['INTEGER_POSITIVE', 'INTEGER', 'INTEGER_ZERO_OR_POSITIVE', 'NUMBER', 'PERCENTAGE',
                        'INTEGER_ZERO_OR_NEGATIVE']


    # Get the datasets"
    if is_valid_uid(dsParam):
        dataset_filter = "id:eq:"+dsParam
    else:
        dataset_filter = "name:like:"+dsParam

    dataSets = api_source.get('dataSets', params={"paging": "false",
                                                  "fields": "id,name,dataSetElements,periodType,"
                                                            "formType,dataEntryForm,sections,organisationUnits",
                                                  "filter": dataset_filter}).json()['dataSets']
    # Only one dataSet
    if len(dataSets) == 0:
        logger.error("Could not find any dataset")
        exit(1)
    else:
        if len(dataSets) > 1 and args.period_type_filter is not None:
            periodTypeFilter = args.period_type_filter
            if periodTypeFilter.lower() not in ['daily', 'weekly', 'monthly', 'quarterly', 'yearly']:
                logger.error('Period type to filter not supported:' + periodTypeFilter)
            else:
                filteredDatasets = list()
                for ds in dataSets:
                    if ds['periodType'].lower() == periodTypeFilter.lower():
                        filteredDatasets.append(ds)
                dataSets = filteredDatasets

        # Create workbook
        if args.create_flat_file is not None:
            ouput_file_name = 'datasets_'+dsParam+'.xlsx'
            ouput_file_name = args.create_flat_file+'.xlsx'
            writer = pd.ExcelWriter(ouput_file_name)
        for ds in dataSets:
            logger.info("Processing dataset " + ds['name'])
            if start_date != "" and end_date != "":
                logger.info("Period type is " + ds[
                    'periodType'] + " - Generating periods from " + start_date + " to " + end_date)
                periods = get_periods(ds['periodType'], start_date, end_date)
            if len(ouUIDs) > 0:
                logger.info("Verifying org unit selection")
                for ou_uid in ouUIDs:
                    if not is_ou_assigned_to_ds(ou_uid, ds):
                        ouUIDs.remove(ou_uid)
                        logger.warning("Org unit " + ou_uid + " is not assigned to dataset " + ds['id'])

            dsDataElements = dict()
            greyedFields = list()

            # Analyse the sections of the dataSet looking for greyedFields
            if 'sections' in ds:
                sectionUIDs = ""
                for section in ds['sections']:
                    sectionUIDs += (section['id'] + ",")
                logger.info("Found " + str(sectionUIDs.count(',')) + " sections in dataset")
                # Get sections
                sections = api_source.get('sections', params={"paging": "false",
                                                              "fields": "id,name,greyedFields[dataElement,categoryOptionCombo]",
                                                              "filter": "id:in:[" + sectionUIDs + "]"}).json()['sections']
                for section in sections:
                    if len(section['greyedFields']) > 0:
                        for element in section['greyedFields']:
                            greyedFields.append(element['dataElement']['id'] + '.' + element['categoryOptionCombo']['id'])

            # Get dataElements
            for DSE in ds['dataSetElements']:
                if 'dataElement' in DSE:
                    deUID = DSE['dataElement']['id']
                    dsDataElements[deUID] = dict()
                    de = DE[deUID]  # Get all dataElement information
                    dsDataElements[deUID]['valueType'] = de['valueType']

                    # Add options to the dataelement dict if pertinent
                    if 'optionSet' in de:
                        options = api_source.get('options',
                                             params={"paging": "false", "fields": "id,name,code",
                                                     "filter": "optionSet.id:eq:"+de['optionSet']['id']}).json()['options']
                        dsDataElements[deUID]['options'] = list()
                        for option in options:
                            dsDataElements[deUID]['options'].append(option['code'])

                    # Check if the Category Combo is specified in the dataElement definition
                    COCs = list()
                    if 'categoryCombo' in de and de['categoryCombo']['id'] != defaultCC:
                        COCs = CC[de['categoryCombo']['id']]['categoryOptionCombos']

                    # Check if Category Combo is specified for the dataElement in the dataSet
                    elif 'categoryCombo' in DSE and DSE['categoryCombo']['id'] != defaultCC:
                        COCs = CC[DSE['categoryCombo']['id']]['categoryOptionCombos']

                    # Add COCs to the dataElement dictionary
                    if len(COCs) > 0:
                        dsDataElements[deUID]['COCs'] = list()
                        for coc in COCs:
                            dsDataElements[deUID]['COCs'].append(coc['id'])

            logger.info("Found " + str(len(dsDataElements)) + " dataElements in dataset")

            if args.create_flat_file is not None:
                for de in dsDataElements:
                    if 'COCs' in dsDataElements[de]:
                        for coc in dsDataElements[de]['COCs']:
                            str_pair = de + "." + coc
                            coc_uid = COC[coc]['id']
                            if 'code' in COC[coc]:
                                coc_code = COC[coc]['code']
                            else:
                                coc_code = ""
                            if str_pair not in greyedFields:
                                df_min_max = df_min_max.append({"DE UID": DE[de]['id'], "COC UID": coc_uid,
                                                                "DE Name": DE[de]['name'], "COC Name": COC[coc]['name'],
                                                                "valueType": dsDataElements[de]['valueType'],
                                                                "min": "", "max": ""}, ignore_index=True)
                    else:
                        df_min_max = df_min_max.append({"DE UID": DE[de]['id'], "COC UID": "DEFAULT",
                                                        "DE Name": DE[de]['name'], "COC Name": "default",
                                                        "valueType": dsDataElements[de]['valueType'],
                                                        "min": "", "max": ""}, ignore_index=True)

                # Save csv file
                # export_csv = df_min_max.to_csv(r'./ds_' + ds['name'].replace(' ', '_') + '_min_max.csv', index=None,
                #                               header=True)
                df_min_max.to_excel(writer, ds['id'], index=False)

            else:
                dataValueSets = list()
                ouCount = 1
                for ouUID in ouUIDs:
                    logger.info("Processing org unit " + ouUID + " - " + str(ouCount) + "/" + str(len(ouUIDs)))
                    for period in periods:
                        #logger.info("Processing period " + period)
                        for de in dsDataElements:
                            value_type = dsDataElements[de]['valueType']
                            min_value = max_value = None
                            options = None
                            if 'options' in dsDataElements[de]:
                                options = dsDataElements[de]['options']
                            if 'COCs' in dsDataElements[de]:
                                for coc in dsDataElements[de]['COCs']:
                                    str_pair = de + "." + coc
                                    if str_pair not in greyedFields:
                                        if df_min_max is not None:
                                            min_value, max_value = get_min_max_from_df(df_min_max, value_type, de, coc)
                                        # logger.info(
                                        #     "Generating value for DE (" + value_type + "): " + DE[de]['name'] + " with COC")
                                        value = generate_dummy_value({'value_type': value_type, 'min_value': min_value,
                                                                            'max_value': max_value, 'options' : options})
                                        if value is not None : # Skip if it is None
                                            dataValueSets.append(
                                                {"dataElement": de, "categoryOptionCombo": coc,
                                                 "value": value, "orgUnit": ouUID, "period": period})
                                    # else:
                                    #     logger.warning('Skipping ' + str_pair + ' because is greyed in section')
                            else:
                                if df_min_max is not None:
                                    min_value, max_value = get_min_max_from_df(df_min_max, value_type, de)
                                # logger.info("Generating value for DE (" + value_type + "): " + DE[de]['name'])
                                value = generate_dummy_value({'value_type': value_type, 'min_value': min_value,
                                                              'max_value': max_value, 'options': options})
                                if value is not None:  # Skip if it is None
                                    dataValueSets.append({"dataElement": de,
                                                          "value": value, "orgUnit": ouUID, "period": period})

                    with open('first_ou_one_week.json', 'w',
                              encoding='utf8') as file:
                        file.write(json.dumps({'dataValues': dataValueSets}, indent=4, sort_keys=True, ensure_ascii=False))
                    file.close()
                    post_to_server({'dataValues': dataValueSets}, 'dataValueSets')
                    dataValueSets = list()
                    ouCount += 1

        if args.create_flat_file is not None:
            writer.save()


if __name__ == '__main__':
    main()
