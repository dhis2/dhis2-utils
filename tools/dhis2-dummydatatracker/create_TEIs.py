from dhis2 import Api, RequestException, setup_logger, logger, generate_uid, is_valid_uid
import json
import pandas as pd
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from faker import Faker
import calendar
from random import randrange, random, choice, uniform, seed, choices, randint
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from gspread_formatting import *
from gspread.exceptions import APIError
from scipy.stats import expon
import re
import uuid
from tools.dhis2 import post_to_server
from tools.json import reindex, json_extract, json_extract_nested_ids
from tools.dd import choices_with_ratio
from tools.dhis2 import post_chunked_data, find_ou_children_at_level
import numpy as np
import logzero
import sys

try:
    f = open("./auth.json")
except IOError:
    print("Please provide file auth.json with credentials for DHIS2 server")
    exit(1)
else:
    api_source = Api.from_auth_file('./auth.json')

program_orgunits = list()
program_teas = list()
program_des = list()
optionSetDict = dict()

trackedEntityType_UID = ""
attributeCategoryOptions_UID = ""
attributeOptionCombo_UID = ""

log_file = "./dummyDataTracker.log"
logzero.logfile(log_file)


scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
google_spreadshseet_credentials = 'dummy-data-297922-97b90db83bdc.json'
try:
    f = open(google_spreadshseet_credentials)
except IOError:
    print("Please provide file with google spreadsheet credentials")
    exit(1)
else:
    credentials = ServiceAccountCredentials.from_json_keyfile_name(google_spreadshseet_credentials, scope)

import argparse
my_parser = argparse.ArgumentParser(description='Create dummy data in an instance using a Google Spreadsheet')
my_parser.add_argument('docid', metavar='document_id', type=str,
                       help='the id of the spreadsheet to use')
args = my_parser.parse_args()

mandatory_sheets = ['DUMMY_DATA', 'NUMBER_REPLICAS', 'PARAMETERS']
try:
    client = gspread.authorize(credentials)
except Exception as e:
    logger.error('Wrong Google Credentials')
    sys.exit()
try:
    sh = client.open_by_key(args.docid)
except Exception as e:
    logger.error('Could not access/find spreadsheet ' + args.docid)
    sys.exit()
try:
    batch = batch_updater(sh)
    all_worksheet = sh.worksheets()
except APIError as e:
    logger.error('Spreadsheet ' + args.docid + ' is no longer accessible (may have been deleted)')
    sys.exit()
worksheet_list = list()
for ws in all_worksheet:
    worksheet_list.append(ws.title)
try:
    for sheet in mandatory_sheets:
        if sheet not in worksheet_list:
            logger.error('Sheet ' + sheet + ' is missing')
            exit(1)

    #df = pd.DataFrame(sh.worksheet("DUMMY_DATA").get_all_records())
    df = get_as_dataframe(sh.worksheet("DUMMY_DATA"), evaluate_formulas=True, dtype=str)
    df = df.dropna(how='all', axis=1)
    df['mandatory'] = df['mandatory'].map({'True':True, 'TRUE':True, 'False':False, 'FALSE':False})

    df_params = get_as_dataframe(sh.worksheet("PARAMETERS"), evaluate_formulas=True, dtype=str)
    df_params = df_params.dropna(how='all', axis=1)
    df_params.fillna('', inplace=True)
    if df_params[df_params.PARAMETER == "server_url"].shape[0] == 1:
        server_url = df_params[df_params.PARAMETER == "server_url"]['VALUE'].tolist()[0]
        if not pd.isnull(server_url) and server_url != "":
            # Whether the file exists has been verified at the beginning of the execution
            with open('./auth.json', 'r') as json_file:
                credentials = json.load(json_file)
            api_source = Api(server_url, credentials['dhis']['username'], credentials['dhis']['password'])
    # server_url = "https://who-dev.dhis2.org/tracker_dev"
    df_number_replicas = get_as_dataframe(sh.worksheet("NUMBER_REPLICAS"), evaluate_formulas=True,
                                          converters={'PRIMAL_ID':str,'NUMBER':int})
    df_number_replicas = df_number_replicas.dropna(how='all', axis=1)
    df_number_replicas.dropna(subset=["NUMBER"], inplace=True)
    df_distrib = None
    if 'DISTRIBUTION' in worksheet_list:
        df_distrib = get_as_dataframe(sh.worksheet("DISTRIBUTION"), evaluate_formulas=True, dtype=str)
        df_distrib = df_distrib.dropna(how='all', axis=1)
        df_distrib.dropna(subset=["VALUE"], inplace=True)
        df_distrib = df_distrib.fillna('')

except:
    logger.error("Something went wrong when processing the spreadsheet")
    logger.error("Unexpected error:", sys.exc_info()[0])
    exit(1)
else:
    logger.info('Google spreadsheet ' + args.docid + ' processed correctly')

# setup_logger()
pd.set_option('display.max_columns', None)


def get_ous_in_distrib(df_ou_distrib, program_ous, org_unit_level):

    def get_ous_in_program(ou_list, program_ous):
        ou_list_as_set = set(ou_list)
        intersection = ou_list_as_set.intersection(set(program_ous))
        return list(intersection)

    # Get values from dataframe
    df_result = df_ou_distrib.copy()
    ou_values = df_ou_distrib['VALUE'].tolist()
    index = 0
    for value in ou_values:
        valid_ou_found = False
        if is_valid_uid(value):
            facilities = find_ou_children_at_level(api_source, value, org_unit_level)
            df_result.at[index, 'VALUE'] = get_ous_in_program(facilities, program_ous)
            valid_ou_found = True
        # Assuming it is a name
        else:
            #Get UID of OU Name:
            ou = api_source.get('organisationUnits', params={'fields':'id,name', 'filter':'name:like:'+value}).json()['organisationUnits']
            if len(ou) == 1:
                ou = ou[0]
                # Find the OUs at the required level
                facilities = find_ou_children_at_level(api_source, ou['id'], org_unit_level)
                df_result.at[index, 'VALUE'] = get_ous_in_program(facilities, program_ous)
                valid_ou_found = True
            else:
                logger.error('Could not find ou with name ' + value)

        if not valid_ou_found:
            logger.error('Could not find any valid organisation unit for value ' + value)

        index += 1

    return df_result


def get_exp_random_dates_from_date_to_today(start_date, end_date = date.today(), k = 10):
    # start_date is in the form datetime.strptime('', '%Y-%m-%d')
    # k = Number of dates to return

    def diff_month(d1, d2):
        return abs((d1.year - d2.year) * 12 + d1.month - d2.month)

    def get_random_date(start_date, end_date, shift):
        lower_date = start_date + relativedelta(months=+shift)
        upper_date = lower_date.replace(day=calendar.monthrange(lower_date.year, lower_date.month)[1])
        if upper_date > end_date:
            upper_date = end_date
        # print(lower_date.strftime('%Y-%m-%d'))
        # print(upper_date.strftime('%Y-%m-%d'))
        return lower_date + timedelta(
            # Get a random amount of seconds between `start` and `end`
            seconds=randint(0, int((upper_date - lower_date).total_seconds())),
        )

    # Number of months included from start_date to the current date
    number_of_months = diff_month(start_date, end_date)
    # Get a simple list with the numbers for each month (0 = month in start_date, 1 = month start date + 1, etc...
    month_numbers = list(range(0, (number_of_months + 1)))
    # Get the exponential weights to be used
    weights = expon.rvs(scale=0.1, loc=0, size=(number_of_months + 1))
    weights.sort()
    # Choose months randomly
    chosen_months = choices(population=month_numbers, weights=weights, k=k)
    # The variable to return is a list
    random_dates = list()
    # Loop through every month selected (defined by first_date of that month, last_date of that month) and find
    # a random day
    for m in chosen_months:
        random_dates.append((get_random_date(start_date, end_date, m)))

    return random_dates


def isTimeFormat(input):
    try:
        datetime.strptime(input, '%H:%M')
        return True
    except ValueError:
        return False


def isDateFormat(input):
    try:
        datetime.strptime(input, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def isLongLat(input):
    result = False
    z = re.match("\[(-*[0-9]{1,3}[.,][0-9]{1,10}),(-*[0-9]{1,2}[.,][0-9]{1,10})\]", input)
    if z:
        longlat = z.groups()
        if len(longlat) == 2 and \
                -180.0 < float(longlat[0].replace(",", ".")) < 180.0 and \
                -90.0 < float(longlat[1].replace(",", ".")) < 90.0:
            result = True
    return result


def validate_value(value_type, value, optionSet = list()):
    # FILE_RESOURCE
    # ORGANISATION_UNIT
    # IMAGE
    # The purpose of this is to make sure the value received is in the right format
    # the spreadsheet values 1 are sometimes converted incorrectly into True, givin a false positive in the validation
    def convert_trueORfalse_to_number(val):
        if val.lower() == 'true' or val is True:
            return '1'
        elif val.lower() == 'false' or val is False:
            return '0'
        else:
            return val

    global program_orgunits

    correct = False


    if len(optionSet) > 0: # It is an option
        value = convert_trueORfalse_to_number(value)
        if value in optionSet:
            correct = True

    elif value_type == 'AGE': # Either an age in years/months/days or a date-of-birth (YYY-MM-DD)
        #if value.isnumeric() and 0 <= int(value) <= 120:
        if isDateFormat(value):
            correct = True
        # todo: check for years/months/days
    elif value_type == 'TEXT': # Text (length of text up to 50,000 characters)
        if len(value) <= 50000:
            correct = True
    elif value_type == 'LONG_TEXT': # Always true
        correct = True
    elif value_type == 'INTEGER_ZERO_OR_POSITIVE':
        value = convert_trueORfalse_to_number(value)
        if value.isnumeric() and 0 <= int(value):
            correct = True
            value = str(int(value)) # Cast float
    elif value_type == 'INTEGER_NEGATIVE':
        if value.isnumeric() and 0 > int(value):
            correct = True
            value = str(int(value))  # Cast float
    elif value_type == 'INTEGER_POSITIVE':
        value = convert_trueORfalse_to_number(value)
        if value.isnumeric() and 0 < int(value):
            correct = True
            value = str(int(value))  # Cast float
    elif value_type == 'INTEGER':
        value = convert_trueORfalse_to_number(value)
        if value.isnumeric():
            correct = True
            value = str(int(value))  # Cast float
    elif value_type == 'NUMBER':
        value = convert_trueORfalse_to_number(value)
        if value.isnumeric():
            correct = True
    elif value_type == 'DATE':
        if isDateFormat(value):
            correct = True
    elif value_type == 'TRUE_ONLY':
        value = value.lower()
        if value == 'true':
            correct = True
        elif value == 1 or value == '1':
            correct = True
            value = 'true'
    elif value_type == 'BOOLEAN':
        value = value.lower()
        if value in ['true', 'false']:
            correct = True
        elif value == 1 or value == '1':
            correct = True
            value = 'true'
        elif value == 0 or value == '0':
            correct = True
            value = 'false'
        elif value in ['yes', 'no']:
            correct = True
    elif value_type == 'TIME':
        if isTimeFormat(value):
            correct = True
    elif value_type == 'PERCENTAGE': # Any decimal value between 0 and 100
        if value.isnumeric() and 0 <= int(value) <= 100:
            correct = True
    elif value_type == 'UNIT_INTERVAL': # Any decimal value between 0 and 1
        if value.isnumeric() and 0 <= int(value) <= 1:
            correct = True
    elif value_type == 'ORGANISATION_UNIT':
        correct = False
        # We could say that people come from a OU which is not assigned to the program
        # so before just that it is a valid DHIS2 UID
        if is_valid_uid(value):
            correct = True
        # for ou in program_orgunits:
        #     if value == ou['id']:
        #         correct = True
    elif value_type == 'PHONE_NUMBER':
        chars = set('0123456789+ ')
        if any((c in chars) for c in value):
            correct = True
    elif value_type == 'COORDINATE':
        # Latitude must be a number between -90 and 90
        # Longitude must a number between -180 and 180
        # Value comes in the form: '[164,72197,-67,617041]'
        correct = isLongLat(value)
    elif value_type == 'EMAIL':
        if re.match(r"[^@]+@[^@]+\.[^@]+", value):
            correct = True
    else:
        logger.info('Warning, type ' + value_type + ' not supported')

    return correct, value


def create_dummy_value(uid, gender='M'):

    def findWholeWord(w):
        return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search

    global program_teas
    global program_des
    if uid == '':
        elem_type = 'enrollmentDate'
        element = dict()
    elif uid in program_teas:
        elem_type = 'tea'
        element = program_teas[uid]
    elif uid in program_des:
        elem_type = 'de'
        element = program_des[uid]
    else:
        elem_type = 'eventDate'
        element = dict()

    faker = Faker()
    Faker.seed()
    value = None
    min_value = -50#dummy_data_params['min_value']
    max_value = 50#dummy_data_params['max_value']
    # If it is not a DE or TEA, it is a enrollmentDate or eventDate, so we initialize to this value
    value_type = 'DATE'
    name = ""
    if elem_type in ['tea', 'de']:
        value_type = element['valueType']
        name = element['name']
    global optionSetDict
    global program_orgunits


    # Define some min / max values for teas
    if elem_type == 'tea':
        if findWholeWord('weight')(name):
            if findWholeWord('birth')(name):
                min_value = 500
                max_value = 5000
            else: # in kg
                min_value = 5.0
                max_value = 150.0

    if 'optionSet' in element:
        optionSet = element['optionSet']['id']
        if optionSet not in optionSetDict:
            options = api_source.get('options', params={"paging": "false",
                                                        "order": "sortOrder:asc",
                                                        "fields": "id,code",
                                                        "filter": "optionSet.id:eq:" + optionSet}).json()[
                'options']
            optionSetDict[optionSet] = json_extract(options, 'code')
        value = choice(optionSetDict[optionSet])

        if elem_type == 'tea' and (findWholeWord('sex')(name) or findWholeWord('gender')(name)):
            # It is an optionSet for sex/gender
            # Male, M, MALE
            # Female, F, FEMALE
            # Transgender, TG
            # Other, OTHER
            # Unknown, UNKNOWN
            # if len(optionSetDict[optionSet]) > 2: # More genders than male/female
                #Introduce other with low probability
                # if randrange(0, 1000) < 50:
                #     gender = 'O'

            for option in optionSetDict[optionSet]:
                if gender == 'M' and option.lower() in ['male', 'm']:
                    value = option
                elif gender == 'F' and option.lower() in ['female', 'f']:
                    value = option
                elif gender == 'O' and option.lower() in ['other']:
                    value = option
                elif gender == 'U' and option.lower() in ['unknown']:
                    value = option
                elif gender == 'T' and option.lower() in ['transgender', 'tg']:
                    value = option

    elif value_type == "BOOLEAN":
        value = choice(['true', 'false'])

    elif value_type == "TRUE_ONLY":
        # If present, it should be True, although if the user has unchecked it, it will be false
        value = choice(['true', None])

    elif value_type == "DATE":
        min_value = date(year=2015, month=1, day=1)
        max_value = datetime.today()
        value = faker.date_between(start_date=min_value, end_date=max_value).strftime("%Y-%m-%d")

    elif value_type == "TIME":
        value = faker.time()[0:5]  # To get HH:MM and remove SS

    elif value_type in ["TEXT", "LONG_TEXT"]:
        # Default behavior for
        value = faker.text()[0:100]
        # teas use TEXT for many standard person attributes
        if elem_type == 'tea':
            if 'pattern' in element and element['pattern'] != "":
                # We don't support yet generating patters
                # ORG_UNIT_CODE(...) + "/" + SEQUENTIAL(  ###)
                value = ""
            else:
                name_to_check = name.replace(" ", "").lower()
                if 'name' in name_to_check:
                    if any(word in name_to_check for word in ['given', 'first']):
                        if gender == 'M':
                            value = faker.first_name_male()
                        elif gender == 'F':
                            value = faker.first_name_female()
                        else:
                            value = faker.first_name()
                    elif any(word in name_to_check for word in ['family', 'last']):
                        value = faker.last_name()
                    else:
                        value = faker.name()
                elif findWholeWord('id')(name):
                    value = 'ID-' + str(uuid.uuid4().fields[-1])[:7]
                elif findWholeWord('number')(name):
                    value = 'N-' + str(uuid.uuid4().fields[-1])[:7]
                elif findWholeWord('code')(name):
                    value = 'Code' + str(uuid.uuid4().fields[-1])[:4]
                elif 'address' in name_to_check:
                    value = faker.address()
                elif any(word in name_to_check for word in ['job', 'employment', 'occupation']):
                    value = faker.job()
                # This will work if sex is type TEXT, which should not be
                elif any(word in name_to_check for word in ['sex', 'gender']):
                    value = choice(['MALE', 'FEMALE'])
        #     else:
        #         value = faker.text()[0:100]
        # else: # For data elements
        #     value = faker.text()[0:100]

    elif value_type == 'AGE':
        # age_range = choice(['child', 'adolescent', 'adult', 'retired'])
        age_ranges = choice([[1,5*365], [5*365,15*365], [15*365,65*365], [65*365,100*365]])
        today = date.today()

        days = randrange(age_ranges[0], age_ranges[1])
        value = (today - timedelta(days=days)).strftime("%Y-%m-%d")

    elif value_type == "INTEGER_POSITIVE":
        min_value = 1
        value = randrange(min_value, max_value)

    elif value_type == "INTEGER_ZERO_OR_POSITIVE":
        min_value = 0
        value = randrange(min_value, max_value)

    elif value_type == "INTEGER_NEGATIVE":
        max_value = -1
        value = randrange(min_value, max_value)

    elif value_type == "INTEGER":
        value = randrange(min_value, max_value)

    elif value_type == "NUMBER":
        value = round(uniform(min_value, max_value), 2)

    elif value_type == 'PERCENTAGE': # Any decimal value between 0 and 100
        value = round(uniform(0, 100), 2)

    elif value_type == 'UNIT_INTERVAL': # Any decimal value between 0 and 1
        value = round(uniform(0, 1), 2)

    elif value_type == 'ORGANISATION_UNIT':
        random_ou = choice(program_orgunits)
        value = random_ou['parent']['id'] # Assign OU from where the patient is coming to the parent

    elif value_type == 'PHONE_NUMBER':
        value = faker.phone_number()
        strs, replacements = value, {"-": " ", "(": "", ")": "", "x": "", "(": "", ".": " "}
        value = "".join([replacements.get(c, c) for c in strs])

    elif value_type == 'COORDINATE':
        #form: '[164,72197,-67,617041]'
        value = '[' + str(round(np.random.uniform(-180, 180),6)) + ',' + str(round(np.random.uniform(-90, 90),6)) + ']'
    else:
        logger.info('Warning, type ' + value_type + ' not supported')

    return value


def check_mandatory_elements_are_present(df, column):
    df_only_true_mandatory = df[df['mandatory'] == True]
    if df_only_true_mandatory[column].count() != df_only_true_mandatory.shape[0]: # If any of the them is missing
        return False
    else:
        return True


def check_unique_attributes_do_not_repeat(df):
    global program_teas
    correct = True
    stage_indexes = df.index[df['Stage'].notnull()].tolist()
    df_enrollment = df[stage_indexes[1]:(stage_indexes[1])]
    tei_columns = [col for col in df_enrollment if col.startswith('TEI_')]
    duplicateRowsDF = df_enrollment[df_enrollment.duplicated(tei_columns)]
    if duplicateRowsDF.shape[0] > 0:
        for index, row in duplicateRowsDF.iterrows():
            if row['UID'] in program_teas and program_teas[row['UID']]['unique'] == 'true':
                logger.error('Unique TEA (' + row['UID'] + '): ' + program_teas[row['UID']]['name'] + ' has duplicate values')
                correct = False
    return correct


def check_template_TEIs_in_cols(df, ws_dummy_data = None):
    import xlsxwriter
    writer = pd.ExcelWriter('Validation results.xlsx', engine='xlsxwriter')
    # Convert the dataframe to an XlsxWriter Excel object.
    df.to_excel(writer, sheet_name='Validation results', index=False)
    workbook = writer.book
    worksheet = writer.sheets['Validation results']
    error_format = workbook.add_format({'bold': True, 'fg_color': 'red', 'border': 1})

    if ws_dummy_data is not None:
        error_cell_fmt = CellFormat(backgroundColor=Color(1, 0, 0))

    # Clear previous errors if applicable from spreadsheet
    try:
        df_valitation_results = get_as_dataframe(sh.worksheet("VALIDATION_RESULTS"), dtype=str)
        for index, row in df_valitation_results.iterrows():
            if 'CELL' in row:
                cell = row['CELL']
                if not pd.isnull(cell[1:]):
                    row_number = int(cell[1:])
                    if row_number % 2 == 0: # Even rows in white
                        batch.format_cell_range(ws_dummy_data, cell + ':' + cell,
                                                CellFormat(backgroundColor=Color(1, 1, 1)))
                    else: # Odd rows in light blue
                        batch.format_cell_range(ws_dummy_data, cell + ':' + cell,
                                                CellFormat(backgroundColor=Color(0.90, 0.95, 1)))
        batch.execute()
    except gspread.WorksheetNotFound:
        pass


    # Write the column headers with the defined format.
    # for col_num, value in enumerate(df.columns.values):
    #     worksheet.write(0, col_num + 1, value, header_format)

    tei_columns = [col for col in df if col.startswith('TEI_')]
    stage_indexes = df.index[df['Stage'].notnull()].tolist()
    errors = 0
    stage_counter = dict()
    df_validation_results = pd.DataFrame({'CELL': [], 'ERROR': []})
    for i in range(0, len(stage_indexes)):
        if (i + 1) != len(stage_indexes):
            df_event = df[stage_indexes[i]:(stage_indexes[i + 1])]
        else:
            df_event = df[stage_indexes[i]:]

        stage_name = df_event.iloc[0]['Stage']
        occurrence = ''
        if stage_name not in stage_counter:
            stage_counter[stage_name] = 1
        else:
            stage_counter[stage_name] += 1
            occurrence = '_' + str(stage_counter[stage_name])

        for tei_column in tei_columns:

            if df_event[tei_column].count() > 0:

                if i == 0:  # Enrollment
                    if df_event[tei_column].count() == 0:
                        # If no data for enrollment, raise error
                        logger.error(tei_column + ': is missing enrollment data')
                        errors = errors + 1

                # Check mandatory elements are present
                # correct = check_mandatory_elements_are_present(df_event, tei_column)
                # if not correct:
                #     logger.error(tei_column + ', Stage=' + stage_name + occurrence + ': Missing mandatory data')
                #     errors = errors + 1

                first_row = True
                for index, row in df_event.iterrows():
                    if not pd.isnull(row[tei_column]):
                        # if first_row:
                        #     correct, value = validate_value('DATE', row[tei_column])
                        #     if not correct:
                        #         worksheet.write(index, df.columns.get_loc(tei_column) + 1, value, error_format)
                        #         logger.error(tei_column + ', Stage=' + stage_name + occurrence + ': Value for event DATE = ' + str(value) + ' is NOT valid')
                        #         errors = errors + 1
                        #     else:
                        #         df.at[index, tei_column] = value
                        # else:
                        # Try to get option codes to use for the DE from the spreadsheet (it would be probably
                        # a better idea to use the API
                        optionSet_list = list()
                        if not pd.isnull(row['optionSet']): optionSet_list = row['optionSet'].split("\n")
                        optionSet_list = [x.strip() for x in optionSet_list]
                        correct, value = validate_value(row['valueType'], row[tei_column],
                                                            optionSet_list)
                        if not correct:
                            error_message = tei_column + ', Stage=' + stage_name + occurrence + ': Value (' + row['valueType'] + ') for ' + row['TEA / DE / eventDate'] + ' = ' + str(value) + ' is NOT valid'
                            logger.error(error_message)
                            errors = errors + 1
                            worksheet.write(index+1, df.columns.get_loc(tei_column), value, error_format)
                            if ws_dummy_data is not None:
                                ws_col_row = chr(65+df.columns.get_loc(tei_column))+str(index+2)
                                try:
                                    batch.format_cell_range(ws_dummy_data, ws_col_row + ':' + ws_col_row, error_cell_fmt)
                                    # gsf.format_cell_range(ws_dummy_data, ws_col_row + ':' + ws_col_row, error_cell_fmt)
                                except APIError as e:
                                    logger.error(e.code + ':' + e.message)
                                    pass
                                df_validation_results = df_validation_results.append({"CELL": ws_col_row,
                                                                                      "ERROR": error_message},
                                                                                     ignore_index=True)
                        else:
                            df.at[index, tei_column] = value
                    else:
                        if row['mandatory'] == True:
                            error_message = tei_column + ', Stage=' + stage_name + occurrence + ': Value (' + row['valueType'] + ') for ' + row['TEA / DE / eventDate'] + ' is missing'
                            logger.error(error_message)
                            errors = errors + 1
                            worksheet.write(index + 1, df_event.columns.get_loc(tei_column), '', error_format)
                            if ws_dummy_data is not None:
                                ws_col_row = chr(65+df.columns.get_loc(tei_column))+str(index+2)
                                try:
                                    batch.format_cell_range(ws_dummy_data, ws_col_row + ':' + ws_col_row, error_cell_fmt)
                                    #gsf.format_cell_range(ws_dummy_data, ws_col_row + ':' + ws_col_row, error_cell_fmt)
                                except APIError as e:
                                    logger.error(e.code + ':' + e.message)
                                    pass
                                df_validation_results = df_validation_results.append({"CELL": ws_col_row,
                                                                                      "ERROR": error_message},
                                                                                     ignore_index=True)
                    first_row = False

    # Delete the worksheet for validation because there were no errors or just to add a new one
    try:
        sh.del_worksheet(sh.worksheet("VALIDATION_RESULTS"))
    except gspread.WorksheetNotFound:
        pass
    if errors > 0:
        logger.error('Found ' + str(errors) + ' errors!!!')
        batch.execute()
        # Delete worksheet for validation. Capture exception does not exist and pass
        ws_validation = sh.add_worksheet('VALIDATION_RESULTS', df_validation_results.shape[0], df_validation_results.shape[1])
        set_with_dataframe(ws_validation, df_validation_results)
        set_column_width(ws_validation, 'B:', 800)
        # Close the Pandas Excel writer and output the Excel file.
        writer.save()
        return False
    else:
        return True


def from_df_to_TEI_json(df_replicas, tei_template, event_template, df_ou_ratio=None):

    global program_uid
    global program_orgunits
    global trackedEntityType_UID
    global attributeCategoryOptions_UID
    global attributeOptionCombo_UID
    global df_distrib

    tei_columns = [col for col in df_replicas if col.startswith('TEI_')]
    logger.info('Found ' + str(len(tei_columns)) + ' TEIs in file')
    list_of_TEIs = list()

    ou_values = list()
    if df_ou_ratio is not None:
        for ou_list in df_ou_ratio['VALUE'].tolist():
            ou_values.append(choice(ou_list))
        ou_values = choices_with_ratio(ou_values, df_ou_ratio['RATIO'].tolist(), len(tei_columns))

    # The indexes where every stage starts
    stage_indexes = df_replicas.index[df_replicas['Stage'].notnull()].tolist()
    for tei_column in tei_columns:
        tei = tei_template.copy()
        # UIDs to generate
        trackedEntityInstance_UID = generate_uid()
        logger.info('Creating TEI = ' + trackedEntityInstance_UID)
        enrollment_UID = generate_uid()

        # Fill out the values known
        # Random selection of OU for this TEI
        if len(ou_values) == 0:
            random_ou = choice(program_orgunits)
        # Use OU distribution for the TEI
        else:
            # Be careful here, this should normally give an int but...
            random_ou = dict()
            random_ou['id'] = ou_values[int(tei_column.split("_")[1])-1]

        tei["trackedEntityInstance"] = trackedEntityInstance_UID
        tei["trackedEntityType"] = trackedEntityType_UID
        tei["orgUnit"] = random_ou['id']

        # Slice df per enrollment/stage
        for i in range(0, len(stage_indexes)):
            if (i + 1) != len(stage_indexes):
                df_event = df_replicas[stage_indexes[i]:(stage_indexes[i + 1])]
            else:
                df_event = df_replicas[stage_indexes[i]:]
            # df_event = df_event.fillna('')

            if i == 0:  # Enrollment
                tei["enrollments"] = list()
                tei["enrollments"].append({"enrollment": enrollment_UID, "trackedEntity": trackedEntityType_UID,
                                           "orgUnit": random_ou['id'], "program": program_uid,
                                           "trackedEntityInstance": trackedEntityInstance_UID,
                                           "coordinate": {"latitude": "", "longitude": ""},
                                           "events": list()})
                current_enrollment = tei["enrollments"][len(tei["enrollments"]) - 1]

                # Add attributes and enrollment date
                first_row = True
                for index, row in df_event.iterrows():
                    value = row[tei_column]
                    if first_row:
                        logger.info('Enrolling TEI on ' + row[tei_column])
                        current_enrollment["enrollmentDate"] = value
                        tei['attributes'] = list()
                        first_row = False
                    else:
                        if not pd.isnull(value) and value != "":
                            tei['attributes'].append({'attribute': row['UID'], 'value': value})

            else:  # Stage
                if (df_event[tei_column] == '').sum() != len(df_event[tei_column]) and \
                        df_event[tei_column].count() > 0:
                    new_event = event_template.copy()
                    new_event["program"] = program_uid
                    new_event["event"] = generate_uid()
                    new_event["orgUnit"] = random_ou['id']
                    new_event["trackedEntityInstance"] = trackedEntityType_UID
                    new_event["enrollment"] = enrollment_UID
                    # new_event["orgUnitName"] = random_ou['name']
                    new_event["attributeCategoryOptions"] = attributeCategoryOptions_UID
                    new_event["attributeOptionCombo"] = attributeOptionCombo_UID
                    # Add data elements and event date
                    first_row = True
                    for index, row in df_event.iterrows():
                        value = row[tei_column]
                        if first_row:
                            logger.info('Creating stage ' + df_event.iloc[0]['Stage'] + ' on ' + row[tei_column])
                            new_event["eventDate"] = value
                            new_event["programStage"] = row['UID']
                            new_event['dataValues'] = list()
                            first_row = False
                        else:
                            if not pd.isnull(value) and value != "":
                                new_event['dataValues'].append({'dataElement': row['UID'], 'value': value})

                    current_enrollment["events"].append(new_event)
                # else:
                #     logger.info("No data for " + df_event.iloc[0]['Stage'])

        logger.info('TEI created')
        list_of_TEIs.append(tei)

    return list_of_TEIs


def create_replicas_from_df(df, column, start_date, end_date, number_of_replicas, df_distrib):

    uids_to_distribute = list()
    distributed_values_per_id = dict()
    if df_distrib is not None and not df_distrib.empty:
        uid_positions = df_distrib.index[(df_distrib.UID != '')].tolist()
        uids_to_distribute = list(filter(None, df_distrib['UID'].tolist()))

    # Generate distributed values
    tei_id = column
    for uid in uids_to_distribute:
        uid_pos = df_distrib.index[(df_distrib.UID == uid)].tolist()
        if len(uid_pos) == 1 and tei_id in df_distrib.columns:
            uid_position = uid_pos[0]
            index = uid_positions.index(uid_position)
            if uid_position != uid_positions[len(uid_positions)-1]:
                df_ratio = df_distrib.loc[uid_positions[index]:uid_positions[index + 1] - 1][['VALUE', tei_id]]
            else:
                df_ratio = df_distrib.loc[uid_positions[index]:][['VALUE', tei_id]]
            df_ratio = df_ratio.rename(columns={tei_id: 'RATIO'})
            df_ratio["RATIO"] = pd.to_numeric(df_ratio["RATIO"])
            # Skip empty ratios
            if sum(df_ratio["RATIO"].tolist()) != 0.0:
                distributed_values_per_id[uid] = choices_with_ratio(df_ratio['VALUE'].tolist(),
                                                                    df_ratio['RATIO'].tolist(),
                                                                    number_of_replicas)

    df_replicas = pd.DataFrame()

    # Check if gender and sex are included in the distribution
    gender_uid = ''
    age_uid = ''
    if df_distrib is not None:
        contains_gender = df_distrib.NAME.str.contains(r"\bsex\b|\bgender\b", case=False).tolist()
        if True in contains_gender:
            gender_uid = df_distrib.iloc[contains_gender.index(True)]['UID']
        contains_age = df_distrib.NAME.str.contains(r"date of birth\b|\bage\b", case=False).tolist()
        if True in contains_age:
            age_uid = df_distrib.iloc[contains_age.index(True)]['UID']

    if program_uid in distributed_values_per_id:
        random_dates = distributed_values_per_id[program_uid]
    else:
        random_dates = get_exp_random_dates_from_date_to_today(start_date, end_date, number_of_replicas)
    # enrollment date can be found at least in two ways: it is the first value in the TEI_X column or it is the
    # only row with UID = program_uid
    # Check if enrollment is there
    enrollmentDate = datetime.strptime(df.iloc[0][column], '%Y-%m-%d').date()
    stage_indexes = df.index[df['Stage'].notnull()].tolist()
    for clone in range(1, number_of_replicas+1):
        start_time = time.time()
        logger.info("Creating TEI_" + str(clone))
        new_column = list()
        # days to shift is going to be equal to the number of days between the random date and the enrollment date
        # If the value is negative we are moving the date to the past, otherwise to the future
        days_to_shift = (random_dates[(clone-1)] - enrollmentDate).days

        # We need to decide on the gender beforehand to make sure the attributes make sense
        # First check if it is not distributed. We are going to try to find the whole word sex/gender
        # This might not work for some programs
        if gender_uid != '' and gender_uid in distributed_values_per_id:
            gender = distributed_values_per_id[gender_uid][(clone - 1)][0:1]
        else:
            gender = choice(['M', 'F'])
        for index, row in df.iterrows():
            if index in stage_indexes:
                skipStage = False
            if pd.isnull(row[column]) or skipStage:
                new_column.append('')
            else:
                if row['valueType'] == 'DATE' or (row['valueType'] == 'AGE' and isDateFormat(row[column])):
                    if age_uid != "" and age_uid == row['UID']:
                        # Special case for age, recalculate it
                        dob = datetime.now() - relativedelta(years=distributed_values_per_id[row['UID']][(clone - 1)])
                        new_column.append(dob.strftime("%Y-%m-%d"))
                    else:
                        # Shift all dates
                        new_date = datetime.strptime(row[column], "%Y-%m-%d") + timedelta(days=days_to_shift)
                        # before it was new_date < datetime.today(), but if we check against end_date, it allows
                        # creating events in the future
                        if new_date.date() < end_date:
                            new_column.append(new_date.strftime("%Y-%m-%d"))
                        else:
                            new_column.append('')
                            if index in stage_indexes:
                                skipStage = True
                                logger.warning("Skipping stage, date = " + new_date.strftime("%Y-%m-%d"))
                else:
                    if index >= stage_indexes[1]:
                        # Do not do anything for stage data for now, unless ratios have been defined
                        if row['UID'] in distributed_values_per_id:
                            new_column.append(distributed_values_per_id[row['UID']][(clone-1)])
                        else:
                            new_column.append(row[column])
                    else: # Enrollment
                        if row['UID'] in distributed_values_per_id:
                            new_column.append(distributed_values_per_id[row['UID']][(clone - 1)])
                        else:
                            new_column.append(create_dummy_value(row['UID'], gender))

        df_replicas["TEI_" + str(clone)] = new_column
        logger.warning("--- %s seconds ---" % (time.time() - start_time))

    df_replicas['UID'] = df['UID']
    df_replicas['Stage'] = df['Stage']

    export_csv = df_replicas.to_csv(r'./replicas' + column + '.csv', index=None, header=True)

    return df_replicas


def main():
    # Print DHIS2 Info
    logger.warning("Server source running DHIS2 version {} revision {}"
                   .format(api_source.version, api_source.revision))

    global program_uid
    global program_orgunits
    global trackedEntityType_UID
    global attributeCategoryOptions_UID
    global attributeOptionCombo_UID
    #global filename
    global df_params
    global df
    global df_distrib
    #global number_replicas_file

    if 'PARAMETER' not in df_params.columns.tolist() or 'VALUE' not in df_params.columns.tolist():
        logger.error('Cannot find required columns PARAMETER/VALUE in params file')
        exit(1)
    parameters = ['program_uid', 'orgUnit_uid', 'descendants', 'orgUnit_level', 'ignore_validation_errors',
                  'start_date', 'end_date', 'server_url', 'chunk_size', 'metadata_version']
    mandatory_params = ['program_uid']
    # Assign defaults
    orgUnit_level = 4
    # Deprecated
    custom_orgunits = list()
    orgUnit_descendants = False
    program_metadata_version = 0
    start_date = (date.today() - timedelta(weeks=75))
    end_date = date.today()
    ignore_validation_errors = False
    chunk_size = 60
    for index, row in df_params.iterrows():
        param = row['PARAMETER']
        if param == "":
            continue
        if param not in parameters:
            logger.warning('Unknown parameter: ' + str(param))
            continue
        if param in mandatory_params:
            mandatory_params.remove(param)
        if param == "program_uid":
            if row['VALUE'] != "" and is_valid_uid(row['VALUE']):
                program_uid = row['VALUE']
            else:
                logger.error('No value provided for program_uid parameter or not a DHIS2 UID')
                exit(1)
        if param == "metadata_version":
            if row['VALUE'] != "" and isinstance(row['VALUE'], str) and row['VALUE'].isnumeric():
                program_metadata_version = int(row['VALUE'])
        if param == "chunk_size":
            if row['VALUE'] != "" and isinstance(row['VALUE'], str) and row['VALUE'].isnumeric():
                chunk_size = int(row['VALUE'])
        elif param == 'orgUnit_uid':
            if row['VALUE'] != "" and is_valid_uid(row['VALUE']):
                custom_orgunits = row['VALUE'].split(',')
        elif param == 'orgUnit_level' and row['VALUE'].isnumeric():
            orgUnit_level = int(row['VALUE'])
        elif param == 'descendants':
            if isinstance(row['VALUE'], bool):
                orgUnit_descendants = row['VALUE']
            elif isinstance(row['VALUE'], str) and row['VALUE'].lower() in ['true', 'false']:
                orgUnit_descendants = bool(row['VALUE'])
        elif param == 'ignore_validation_errors':
            if isinstance(row['VALUE'], bool):
                ignore_validation_errors = row['VALUE']
            elif isinstance(row['VALUE'], str) and row['VALUE'].lower() in ['true', 'false']:
                if row['VALUE'].lower() == 'true': ignore_validation_errors = True
        elif param == 'start_date':
            if isinstance(row['VALUE'], str):
                if isDateFormat(row['VALUE']):
                    start_date = datetime.strptime(row['VALUE'], '%Y-%m-%d').date()
            else:
                start_date = row['VALUE'].date()
        elif param == 'end_date':
            if isinstance(row['VALUE'], str):
                if isDateFormat(row['VALUE']):
                    end_date = datetime.strptime(row['VALUE'], '%Y-%m-%d').date()
            else:
                end_date = row['VALUE'].date()

    if start_date > end_date:
        logger.error('Start and End dates are wrong')
        exit(1)
    if len(mandatory_params) > 0:
        logger.error('Missing mandatory parameters: ' + ','.join(mandatory_params))
        exit(1)

    program = api_source.get('programs/'+program_uid,
                             params={"paging": "false",
                                     "fields": "id,name,enrollmentDateLabel,version,programTrackedEntityAttributes,programStages,programRuleVariables,organisationUnits,trackedEntityType"}).json()

    if isinstance(program, dict):
        # Check metadata version
        if program_metadata_version != 0 and program_metadata_version != program['version']:
            logger.warning("The flat file was created with program version = " + str(program_metadata_version) +
                         ' but the current version for this program is ' + str(program['version']))
            #exit(1)

        trackedEntityType_UID = program['trackedEntityType']['id']

        # Get orgUnits of program
        orgunits_uid = json_extract(program['organisationUnits'], 'id')
        all_orgunits_at_level = api_source.get('organisationUnits',
                                  params={"paging": "false",
                                          "filter": "level:eq:"+str(orgUnit_level),
                                          "fields":"id,name,level,parent"}).json()['organisationUnits']
        program_orgunits = list()
        for ou in all_orgunits_at_level:
            if ou['id'] in orgunits_uid:
                program_orgunits.append(ou)

        df_ou_distrib = None
        if df_distrib is not None and df_distrib[df_distrib.NAME == 'Organisation Unit'].shape[0] > 0:
            ou_pos = df_distrib.index[(df_distrib.NAME == 'Organisation Unit')].tolist()
            if len(ou_pos) == 1:
                ou_pos = ou_pos[0]
                all_positions = df_distrib.index[(df_distrib.NAME != '')].tolist()
                index = all_positions.index(ou_pos)
                if ou_pos != all_positions[len(all_positions) - 1]:
                    df_ou_distrib = df_distrib.loc[all_positions[index]:all_positions[index + 1] - 1]
                else:
                    df_ou_distrib = df_distrib.loc[all_positions[index]:]
                df_ou_distrib = get_ous_in_distrib(df_ou_distrib.reset_index(drop=True), orgunits_uid, orgUnit_level)


        # We are assuming here that there is going to be always a default value for CO and COC
        attributeCategoryOptions_UID = api_source.get('categoryOptions',
                                                      params={"filter":"name:in:[default,DEFAULT]"}).json()['categoryOptions'][0]['id']
        # We are assuming here that there is going to be always a default value for CO and COC
        attributeOptionCombo_UID = api_source.get('categoryOptionCombos',
                                                      params={"filter":"name:in:[default,DEFAULT]"}).json()['categoryOptionCombos'][0]['id']

        # Get Program Attributes
        teas_uid = json_extract_nested_ids(program, 'trackedEntityAttribute')
        global program_teas
        program_teas = api_source.get('trackedEntityAttributes',
                                      params={"paging": "false",
                                              "fields": "id,name,aggregationType,valueType,unique,optionSet,mandatory,pattern",
                                              "filter": "id:in:[" + ','.join(teas_uid) + "]"}).json()[
            'trackedEntityAttributes']
        program_teas = reindex(program_teas, 'id')

        ##########################
        # Open CSV as df
        # df = pd.read_csv(filename, sep=None, engine='python')

        # Get Program Data Elements - Use the df because it is faster and easier than looking at the programStages..
        global program_des
        dataelement_uids = list(dict.fromkeys(df['UID'].dropna().tolist()))
        number_elems = len(dataelement_uids)
        chunk_max_size = 50
        chunk = dict()
        if number_elems < chunk_max_size:
            chunk_max_size = number_elems
        count = 0
        program_des = list()
        for x in range(0, number_elems, chunk_max_size):
            chunk = dataelement_uids[x:(
                (x + chunk_max_size) if number_elems > (x + chunk_max_size) else number_elems)]
            count += 1

            program_des += api_source.get('dataElements',
                                          params={"paging": "false",
                                                  "fields": "id,name,aggregationType,valueType,optionSet",
                                                  "filter": "id:in:[" + ','.join(chunk) + "]"}).json()[
                'dataElements']
        program_des = reindex(program_des, 'id')

        # Check unique attributes are not repeating
        correct = check_unique_attributes_do_not_repeat(df)
        if not correct:
            exit(1)
        # Validate values of TEIs
        correct = check_template_TEIs_in_cols(df, sh.worksheet("DUMMY_DATA"))
        if not correct and ignore_validation_errors == False:
            exit(1)

        # print(df)
        # print(df.info())

        #df_out = df[['UID', 'TEI_1']].apply(lambda x: create_dummy_value(x['UID']), axis=1)

        # Open TEI template
        with open('TEI_template.json', 'r') as f:
            tei_template = json.load(f)
        # Get template for events and restart the list
        event_template = tei_template['enrollments'][0]['events'][0]
        tei_template['enrollments'] = list()
        tei_template['attributes'] = list()

        list_of_TEIs = list()
        for index, row in df_number_replicas.iterrows():
            tei_id = row['PRIMAL_ID']
            if tei_id in df.columns and isinstance(row['NUMBER'], int):
                if row['NUMBER'] == 0:
                    continue
                logger.info('Creating ' + str(row['NUMBER']) + ' replicas for ' + tei_id)
                start_time = time.time()
                # todo: check if df_distrib has actual date on it
                if df_ou_distrib is not None and tei_id in df_ou_distrib.columns:
                    df_ratio = df_ou_distrib[['VALUE', tei_id]]
                    df_ratio = df_ratio.rename(columns={tei_id: 'RATIO'})
                    df_ratio["RATIO"] = pd.to_numeric(df_ratio["RATIO"])
                    if sum(df_ratio["RATIO"].tolist()) == 0.0:
                        df_ratio = None
                else:
                    df_ratio = None
                replicas = from_df_to_TEI_json(create_replicas_from_df(df, tei_id, start_date, end_date, row['NUMBER'], df_distrib), tei_template, event_template, df_ratio)
                post_chunked_data(api_source, replicas, 'trackedEntityInstances', chunk_size)
                #post_to_server(api_source, {'trackedEntityInstances': replicas}, 'trackedEntityInstances')
                list_of_TEIs = list_of_TEIs + replicas
                logger.info("--- Elapsed time = %s seconds ---" % (time.time() - start_time))
            else:
                if tei_id not in df.columns:
                    if not pd.isnull(tei_id) and tei_id != "":
                        logger.warning('The PRIMAL_ID ' + tei_id + ' in NUMBER_REPLICAS do not match the IDs in DUMMY DATA:')
                    [logger.warning(col) for col in df.columns.tolist() if 'TEI_' in col]

                else:
                    logger.warning('Value ' + str(row['NUMBER']) + ' in row ' + tei_id + ' is not valid... Skipping')

        #post_to_server(api_source, {'trackedEntityInstances': list_of_TEIs}, 'trackedEntityInstances')

        # logger.info(json.dumps(list_of_TEIs, indent=4)) # , sort_keys=True))

        dateTimeObj = datetime.now()
        timestampStr = dateTimeObj.strftime("%d-%b-%Y_%H-%M-%S")
        with open('trackedEntityInstances_' + program_uid + '_' + timestampStr + '.json', 'w') as file:
            file.write(json.dumps({'trackedEntityInstances': list_of_TEIs}, indent=4))
        file.close()


if __name__ == '__main__':
    main()