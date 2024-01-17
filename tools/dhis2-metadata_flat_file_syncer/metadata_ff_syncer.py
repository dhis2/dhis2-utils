import time
from flask import Flask, request, render_template, redirect, url_for
import flask
from flask_cors import CORS
import json
import re
import os
import pandas as pd
import numpy as np
from dhis2 import RequestException, Api, setup_logger, logger
from urllib.request import urlopen
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from gspread_formatting import *
from gspread.exceptions import APIError
from os.path import exists
import validators
import sys
from argparse import ArgumentParser


def authorize_google_sheets(auth_file):
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    try:
        f = open(auth_file)
    except IOError:
        print("Please provide file with google spreadsheet credentials")
        exit(1)
    else:
        credentials = ServiceAccountCredentials.from_json_keyfile_name(auth_file, scope)
    try:
        return gspread.authorize(credentials)
    except Exception as e:
        logger.error('Wrong Google Credentials')
        exit()


app = Flask(__name__)
CORS(app)

def create_app(config_file):
    # app = Flask(__name__)
    # CORS(app)
    app.config['CONFIG_FILE'] = config_file
    print('Using configuration file: ', app.config['CONFIG_FILE'])
    return app


def reindex(json_object, key):
    new_json = dict()
    for elem in json_object:
        key_value = elem[key]
        # elem.pop(key)
        new_json[key_value] = elem
    return new_json


def get_metadata_element(api, metadata_type, filter="", fields=':owner'):
    params = {"paging": "false",
              "fields": fields}
    if filter != "":
        params["filter"] = filter
    try:
        # if the filter is too long, i.e. too many ids, we chunk it to avoid causing a 414 or 400 error
        if len(filter) > 1000:
            filter_list = filter.split(':')
            if len(filter_list) == 3:  # Eg id:in:[id1,id2] should have 3 elements
                id_list = filter_list[2].replace('[', '').replace(']', '').split(',')
                metadata_result = list()
                number_elems = len(id_list)
                # The goal is is to extract the uids in the filter into a list again and then
                # chunk that list in pieces of 100 which can be used in the API call to make sure it works now
                # Jenkins seems to have problems when it is set to 100
                chunk_max_size = 75
                for x in range(0, number_elems, chunk_max_size):
                    chunk_ids = id_list[x:(
                        (x + chunk_max_size) if number_elems > (x + chunk_max_size) else number_elems)]
                    metadata_result += get_metadata_element(metadata_type,
                                                            filter_list[0] + ":" + filter_list[1] + ":[" +
                                                            ','.join(chunk_ids) + "]")
                return metadata_result
        else:
            return api.get(metadata_type, params=params).json()[metadata_type]
    except RequestException as e:
        logger.error('Server return ' + str(e.code) + ' when getting ' + metadata_type)
        # if e.code == 414 or e.code == 400:
        sys.exit(1)

    return []


def log_msg(msg, type='info'):
    print(str(msg))


def post_to_server(api, jsonObject, apiObject='metadata', strategy='CREATE_AND_UPDATE', mergeMode='MERGE'):
    def compose_error_after_failed_post(e):
        error_text = ""
        if 'httpStatus' in e and int(e['httpStatusCode']) > 399:
            error_text += e['httpStatus'] + ": " + str(e['httpStatusCode']) + "<br>"
        if 'message' in e:
            error_text += e['message'] + "<br>"
        if 'response' in e:
            response = e['response']
            if 'stats' in response:
                error_text += str(response['stats']) + "<br>"
            if 'typeReports' in response:
                for type_report in response["typeReports"]:
                    for object_report in type_report["objectReports"]:
                        for error_report in object_report["errorReports"]:
                            error_text += error_report["message"] + "<br>"
        return error_text

    result = { 'type': 'info', 'msg': ""}
    try:
        response = api.post(apiObject, params={'mergeMode': mergeMode, 'importStrategy': strategy},
                                   json=jsonObject)

    except RequestException as e:
        error_message = str(e)
        error_message = error_message[error_message.find("description:") + len("description:"):]
        error_message = error_message.strip()
        error_dict = json.loads(error_message)
        print('error_dict:\n' + str(error_dict))
        if mergeMode == 'REPLACE':
            result['type'] = 'error'
            result['msg'] = compose_error_after_failed_post(error_dict)
            return result
        else:
            # Try with REPLACE
            # print('mergeMode FAILED :' + str(e))
            result = post_to_server(api, jsonObject, mergeMode='REPLACE')
            return result

    else:
        if response is None:
            result['type'] = 'error'
            result['msg'] = "Error in response from server"
            return result

        text = json.loads(response.text)
        print('text:\n' + str(text))
        if 'status' in text and text['status'] == 'ERROR':
            result['type'] = 'error'
            result['msg'] = "Import failed!!!!\n" + json.dumps(text['typeReports'], indent=4, sort_keys=True)
            with open('post_error.json', 'w') as f:
                json.dump(text['typeReports'], f, indent=4, sort_keys=True)
            return result
        # errorCode = errorReport['errorCode']
        else:
            if apiObject == 'metadata':
                result['type'] = 'info'
                if 'stats' in text:
                    result['msg'] = "metadata imported " + text['status'] + " " + json.dumps(text['stats'])
                elif 'response' in text and 'stats' in text['response']:
                    result['msg'] = "metadata imported " + text['status'] + " " + json.dumps(text['response']['stats'])
            else:
                result['type'] = 'info'
                result['msg'] = "Data imported\n" + json.dumps(text, indent=4, sort_keys=True)
                with open('post_error.json', 'w') as f:
                    json.dump(text, f, indent=4, sort_keys=True)

            return result


def get_json_payload_to_instance(api, metadata_type, json_payload, index_elements_to_delete = []):
    if len(index_elements_to_delete) > 0:
        tmp_payload = list()
        for i in range(0, len(json_payload)):
            if i in index_elements_to_delete:
                # Delete
                uid = json_payload[i]['id'][-11:]
                try:
                    response = api.delete(metadata_type + '/' + uid)
                except RequestException as e:
                    if e.code == 404:
                        pass
                    else:
                        # logger.error(e)
                        log_msg(str(e), 'error')
                    pass
                else:
                    # logger.info(args.metadata_type + " " + uid + " removed")
                    log_msg(metadata_type + " " + uid + " removed")
            else:
                tmp_payload.append(json_payload[i])

        json_payload = tmp_payload

    # ----------------------------------

    return {metadata_type: json_payload}


def extract_multi_level(df, keyword):
    json_payload = dict()
    json_payload[keyword] = []
    if (df.eq('').all().all()):
        return json_payload
    columns = df.columns
    for index, row in df.iterrows():
        new_element = dict()
        for column in columns:
            c = column.replace(keyword + '-', '').replace('[', '').replace(']', '')
            if '-' not in c:
                new_element[c] = row[column]
            else:
                tmp = c.split('-')
                if tmp[0] not in new_element:
                    new_element[tmp[0]] = {tmp[1]:row[column]}
        json_payload[keyword].append(new_element)

    return json_payload


def add_owned_fields_to_json_payload(api, json_payload):

    # Get all metadata for that metadata_type
    metadata_types = json_payload.keys()

    for metadata_type in metadata_types:
        metadata = get_metadata_element(api, metadata_type)
        # Reindex so to have a dictionary whose keys are the metadata uids
        metadata = reindex(metadata, 'id')
        # Loop though the payload and see if there are matches
        for i in range(0, len(json_payload[metadata_type])):
            metadata_object = json_payload[metadata_type][i]
            if 'id' in metadata_object:
                uid = metadata_object['id']
                if uid in metadata:
                    json_payload[metadata_type][i] = {**metadata[uid], **json_payload[metadata_type][i]}

    return json_payload


def add_constant_schemas_to_configuration(api_source, metadata_type, df, mandatory_fields):
    def expand_df_columns_to_fit_new_row(df, new_row):
        if len(df.columns) == 0:
            df = pd.DataFrame(columns=['column' + str(i) for i in range(1, (len(new_row) + 1))])
        elif len(df.columns) < len(new_row):
            for i in range((len(df.columns) + 1), (len(new_row) + 1)):
                column_name = 'column' + str(i)
                if column_name not in df.columns:
                    df[column_name] = [''] * df.shape[0]
        return df

    # Still dont know how to get periodType from schemas
    hardcoded_constants = {
        'periodType': ['Daily','Weekly','Monthly','Quarterly','Yearly','WeeklyWednesday','WeeklyThursday','WeeklySaturday','WeeklySunday','BiWeekly','BiMonthly','SixMonthly','SixMonthlyApril','SixMonthlyNov','FinancialApril','FinancialJuly','FinancialOct','FinancialNov'],
        'boundaryTarget': ['ENROLLMENT_DATE', 'EVENT_DATE']
    }

    # Go from the full name, eg Data Elements to and api endpoint working for schemas
    api_endpoint = metadata_type.strip().replace(' ', '')
    api_endpoint = api_endpoint[0].lower() + api_endpoint[1:]
    if api_endpoint[-3:] == 'ies':
        api_endpoint = api_endpoint[:-3] + 'y'
    elif api_endpoint[-1] == 's':
        api_endpoint = api_endpoint[:-1]
    params = {
        "fields": "properties[name,required,constants]"
    }
    try:
        metadata_properties = api_source.get('schemas/'+api_endpoint,
                                  params=params).json()['properties']
        if api_endpoint == 'programIndicator':
            metadata_properties += api_source.get('schemas/analyticsPeriodBoundary',
                                                 params=params).json()['properties']
    except RequestException as e:
        logger.error('Server return ' + str(e.code) + ' when getting schemas for ' + metadata_type)
        return df, mandatory_fields
    else:
        already_added_constants = False
        for _property in metadata_properties:
            if 'required' in _property and _property['required']:
                if metadata_type not in mandatory_fields:
                    mandatory_fields[metadata_type] = list()
                mandatory_fields[metadata_type].append(_property['name'])

            if 'constants' in _property:
                if not already_added_constants:
                    # Add a row with the metadata_type
                    new_row = ['']*len(_property['constants'])
                    new_row[0] = metadata_type
                    try:
                        df.loc[len(df)] = new_row
                    except ValueError as e:
                        df = expand_df_columns_to_fit_new_row(df, new_row)
                        if len(new_row) < df.shape[1]:
                            new_row += ['']*(df.shape[1]-len(new_row))
                        df.loc[len(df)] = new_row

                    already_added_constants = True
                if 'name' in _property:
                    new_row = [_property['name']] + _property['constants']
                    df = expand_df_columns_to_fit_new_row(df, new_row)
                    if len(new_row) < df.shape[1]:
                        new_row += [''] * (df.shape[1] - len(new_row))
                    df.loc[len(df)] = new_row
            if 'name' in _property and _property['name'] in hardcoded_constants:
                new_row = [_property['name']] + hardcoded_constants[_property['name']]
                df = expand_df_columns_to_fit_new_row(df, new_row)
                if len(new_row) < df.shape[1]:
                    new_row += [''] * (df.shape[1] - len(new_row))
                df.loc[len(df)] = new_row

        return df, mandatory_fields


def apply_formatting_to_worksheet(worksheet, metadata_types_supported, worksheet_names, df_conf, mandatory_fields):
    # sheetId = worksheet._properties['sheetId']
    sheetId = worksheet.id

    if df_conf.shape[0] == 0:
        config_values = list()
    else:
        config_values = list(df_conf.iloc[:,0])
    formatting_rules = {'id': ['=COUNTIF(*:*, *2) > 1'],
                        'name': ['=COUNTIF(*:*, *2) > 1'],
                        'shortName': ['=COUNTIF(*:*, *2) > 1', '=LEN(*2) > 50'],
                        'code': ['=COUNTIF(*:*, *2) > 1']}

    # Get all the column names in the worksheet
    while True:
        try:
            column_names = worksheet.row_values(1)
        except gspread.exceptions.APIError as e:
            time.sleep(30)
            pass
        else:
            break

    # Clear current data validation rules and formatting
    # while True:
    #     try:
    #         worksheet.clear()
    #     except gspread.exceptions.APIError as e:
    #         time.sleep(30)
    #         pass
    #     else:
    #         break

    conditional_formatting_rule_index = 0

    # Create a list of requests to apply formatting to the first row
    ##### Bold format, text align center and freeze first row
    requests = [
        {
            "repeatCell": {
                "range": {
                  "sheetId": sheetId,
                  "startRowIndex": 0,
                  "endRowIndex": 1
                },
                "cell": {
                      "userEnteredFormat": {
                            # "backgroundColor": {
                            #   "red": 0.0,
                            #   "green": 0.0,
                            #   "blue": 0.0
                            # },
                            "horizontalAlignment": "CENTER",
                            "textFormat": {
                                # "foregroundColor": {
                                #     "red": 1.0,
                                #     "green": 1.0,
                                #     "blue": 1.0
                                # },
                                # "fontSize": 12,
                                "bold": True
                            }
                     }
                },
                "fields": "userEnteredFormat(textFormat,horizontalAlignment)"
                #"fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
            }
        },
        # Replace APOSTROPHE with '. See comment on APOSTROPHE
        {
            "findReplace": {
                "sheetId": sheetId,
                "find": "APOSTROPHE",
                "replacement": "'",
                "matchEntireCell": False
                #"allSheets": True
            }
        },
        {
              "updateSheetProperties": {
                    "properties": {
                      "sheetId": sheetId,
                      "gridProperties": {
                        "frozenRowCount": 1
                      }
                    },
                    "fields": "gridProperties.frozenRowCount"
              }
        }
    ]

    ### Loop through each column name and add a request to apply italic formatting if it's in mandatory_fields
    for col_index, column_name in enumerate(column_names):
        # Some column names are composed, like [analyticsPeriodBoundaries-analyticsPeriodBoundaryType]
        # For those cases, we need to look for analyticsPeriodBoundaryType
        # So this variable will contain either just the normal name or the column OR
        # the result of removing [ ] and taking the second element after splitting by -
        column_name_for_schema_constant_dropdown_menu = column_name.replace("[","").replace("]","").split('-')
        if len(column_name_for_schema_constant_dropdown_menu) > 1:
            column_name_for_schema_constant_dropdown_menu = column_name_for_schema_constant_dropdown_menu[1]
        else:
            column_name_for_schema_constant_dropdown_menu = column_name_for_schema_constant_dropdown_menu[0]
        if column_name in mandatory_fields:
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheetId,
                        "startRowIndex": 0,
                        "endRowIndex": 1,
                        "startColumnIndex": col_index,
                        "endColumnIndex": col_index + 1
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "textFormat": {
                                "italic": True,
                                "bold": True
                            }
                        }
                    },
                    "fields": "userEnteredFormat(textFormat)"
                }
            })

        ### Add VlOOKUP custom formula for ids
        if '-id' in column_name:
            if column_name.count("-") == 1:
                column_name = column_name.replace('[', '', ).replace(']', '').replace('-id', '')
            else:  # 2 characters -
                column_name = column_name.replace('[', '', ).replace(']', '')
                column_name_list = column_name.split("-")
                column_name = column_name_list[1]
            the_worksheet = ' '.join([word.capitalize() for word in
                                      re.findall(r'[a-zA-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', column_name)])
            if not the_worksheet.endswith("s"):
                the_worksheet += "s"

            if the_worksheet in worksheet_names:
                # cold_index + 2 because we are doing vlookup on the column at the right
                col_letter = gspread.utils.rowcol_to_a1(1, col_index + 2).split('1')[0]
                rows = list()
                for row_index in range(2, worksheet.row_count + 1):
                    formula = "=iferror(VLOOKUP(" + col_letter + str(
                        row_index) + ",{'" + the_worksheet + "'!$B$2:$B, '" + the_worksheet + "'!$A$2:$A}, 2, FALSE), \"\")"

                    rows.append({
                        "values": [
                            {
                                "userEnteredValue": {
                                    "formulaValue": formula
                                }
                            }
                        ]
                    })
                requests.append(
                    {
                        "updateCells": {
                            "range": {
                                "sheetId": sheetId,
                                "startRowIndex": 1,
                                "startColumnIndex": col_index,
                                "endColumnIndex": col_index+1
                            },
                            "rows": rows,
                            "fields": "userEnteredValue"
                        }
                    }
                )

        elif '-name' in column_name:
            # Apply data validation so the names come from another worksheet
            if column_name.count("-") == 1:
                column_name = column_name.replace('[', '', ).replace(']', '').replace('-name', '')
            else:  # 2 characters -
                column_name = column_name.replace('[', '', ).replace(']', '')
                column_name_list = column_name.split("-")
                column_name = column_name_list[1]

            the_worksheet = ' '.join(
                [word.capitalize() for word in re.findall(r'[a-zA-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', column_name)])
            if not the_worksheet.endswith("s"):
                the_worksheet += "s"
            if the_worksheet in worksheet_names and the_worksheet in metadata_types_supported:
                col_letter = gspread.utils.rowcol_to_a1(1, col_index + 1).split('1')[0]

                # Apply data validation to the column in the current sheet
                # We specify column B because we assume that the name is there
                # X_worksheet = sh.worksheet(the_worksheet)
                # num_rows = X_worksheet.row_count
                validation_range = "='" + the_worksheet + "'!$B$2:$B" # $" + str(num_rows)

                requests.append({
                    "setDataValidation": {
                        "range": {
                            "sheetId": sheetId,
                            "startRowIndex": 1,
                            "startColumnIndex": col_index,
                            "endColumnIndex": col_index + 1
                        },
                        "rule": {
                            "condition": {
                                "type": "ONE_OF_RANGE",
                                "values": [
                                    {
                                        "userEnteredValue": validation_range
                                    }
                                ]
                            },
                            "showCustomUi": True,
                            "strict": True
                        }
                    }
                })

        elif column_name in config_values or column_name_for_schema_constant_dropdown_menu in config_values:
            column_name = column_name_for_schema_constant_dropdown_menu
            # Get the letter of the column in the current sheet
            col_letter = gspread.utils.rowcol_to_a1(1, col_index + 1).split('1')[0]

            # Get the index of the header in the Configuration sheet
            config_col_index = config_values.index(column_name)

            # Get the validation values for the current header
            # Get the index of the first occurrence of the metadata_type
            # start_index = config_values.index(worksheet_name)
            # end_index = len(config_values)
            # for metadata_type_index in range(start_index+1, len(config_values)):
            #     if config_values[metadata_type_index] in metadata_types_supported:
            #         end_index = metadata_type_index
            #         break
            # # Extract the slice of the dataframe
            # slice_df = df_conf.iloc[start_index:end_index]
            validation_values = list(df_conf.loc[config_values.index(column_name)])
            validation_values.pop(0)
            values = list()
            for validation_value in validation_values:
                if validation_value != '':
                    values.append({
                                        "userEnteredValue": validation_value
                                    })

            requests.append({
                "setDataValidation": {
                    "range": {
                        "sheetId": sheetId,
                        "startRowIndex": 1,
                        "startColumnIndex": col_index,
                        "endColumnIndex": col_index + 1
                    },
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": [values]
                        },
                        "showCustomUi": True,
                        "strict": True
                    }
                }
            })

        # CONDITIONAL FORMATTING
        # Red if value is not unique for id, name, shortName
        # Red if shortName is > 50
        elif column_name in formatting_rules:
            col_letter = gspread.utils.rowcol_to_a1(1, col_index + 1).split('1')[0]
            for formula in formatting_rules[column_name]:
                # requests.append(
                #         {
                #             "deleteConditionalFormatRule": {
                #                 "index": conditional_formatting_rule_index,
                #                 "sheetId": sheetId
                #             }
                #         }
                # )
                requests.append(
                        {
                            "addConditionalFormatRule": {
                                "index": conditional_formatting_rule_index,
                                "rule": {
                                    "ranges": [
                                        {
                                            "sheetId": sheetId,
                                            "startRowIndex": 1,
                                            "startColumnIndex": col_index,
                                            "endColumnIndex": col_index + 1
                                        }],
                                    "booleanRule": {
                                        "condition": {
                                            "type": "CUSTOM_FORMULA",
                                            "values": [{"userEnteredValue": formula.replace('*', col_letter)}],
                                        },
                                        "format": {
                                            "backgroundColorStyle": {
                                                "rgbColor": {"red": 1, "green": 0, "blue": 0}
                                            }
                                        },
                                    },
                                },
                            }
                        }
                )
                conditional_formatting_rule_index += 1

    return requests


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route('/instances', methods=["GET"])
def instances():
    if exists('instances.conf'):
        instance_file = open("instances.conf", "r")

        instances = list()
        for line in instance_file:
            stripped_line = line.strip()
            if validators.url(stripped_line):
                instances.append(stripped_line)
            else:
                print("URL " + stripped_line + " is not valid")
        instance_file.close()
    else:
        url_sandbox = "https://who.sandbox.dhis2.org/"
        facts_sandbox = "instance_facts.json?v=1652951563817"
        response = urlopen(url_sandbox + facts_sandbox)
        instances_json = json.loads(response.read())
        instances = list()
        for instance in instances_json:
            instances.append(url_sandbox + instance['name'])
        url_metadata = "https://metadata.dev.dhis2.org/"
        facts_metadata = "instance_facts.json?v=1654850549526"
        response = urlopen(url_metadata + facts_metadata)
        instances_json = json.loads(response.read())
        for instance in instances_json:
            instances.append(url_metadata + instance['name'])

    return flask.jsonify(instances)


@app.route('/flatFiles', methods=["GET"])
def flat_files():
    return flask.jsonify(gc.list_spreadsheet_files())

@app.route('/metadataTypes', methods=["GET"])
def metadata_types():
    with open(app.config['CONFIG_FILE']) as file:
        metadata_types = []
        for line in file:
            if len(line) > 0 and ':' in line:
                # metadata_type:columns separated by commas
                fields = line.split(':')
                if fields[0] == 'Programs':
                    metadata_types.append("Programs+Program Stages")
                    continue
                if fields[0] == 'Program Stages' and "Programs+Program Stages" in metadata_types:
                    continue
                if fields[0] == 'Program Rules':
                    metadata_types.append("Program Rules+Program Rule Actions")
                    continue
                if fields[0] == 'Program Rule Actions' and "Program Rules+Program Rule Actions" in metadata_types:
                    continue
                metadata_types.append(fields[0])
    return flask.jsonify(metadata_types)


# Route for handling the login page logic
@app.route('/login')
def login():
    return render_template('login.html')
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     error = None
#     if request.method == 'POST':
#         if request.form['username'] != 'admin' or request.form['password'] != 'admin':
#             error = 'Invalid Credentials. Please try again.'
#         else:
#             return redirect(url_for('home'))
#     return render_template('login.html', error=error)


@app.route('/connectToApi', methods=["POST"])
def connect_to_api():
    global api_source
    received_data = request.get_json()
    instance_url = received_data['url']
    username = received_data['user']
    password = received_data['password']
    try:
        api_source = Api(instance_url, username, password)
        print("Running DHIS2 version {} revision {}".format(api_source.version, api_source.revision))
        base_url = api_source.base_url
    except RequestException as e:
        return flask.jsonify({'msg':'Could not connect to API ' + instance_url, 'type':'error'})
    else:
        print()
        return flask.jsonify({'msg': 'Connected to API in ' + "{}".format(base_url) + ' as user: ' + username, 'type':'info'})


@app.route('/createSpreadsheet', methods=["POST"])
def create_spreadsheet():
    global sh
    received_data = request.get_json()
    gs_file = received_data['gs_file']
    spreadsheet_exists = True

    try:
        sh = gc.open(gs_file)
    except gspread.SpreadsheetNotFound as e:
        spreadsheet_exists = False
        pass

    if spreadsheet_exists:
        return flask.jsonify(
            {'msg': 'The tittle provided for the spreadsheet ' + gs_file + ' already exists', 'type': 'error'})
    else:
        try:
            sh = gc.create(gs_file)
        except Exception as e:
            return flask.jsonify(
                {'msg': "An error occurred: " + str(e), 'type': 'error'})
        else:
            return flask.jsonify(
                {'msg': 'Google spreadsheet ' + "{}".format(gs_file) + ' created successfully', 'type': 'info'})


@app.route('/openSpreadsheet', methods=["POST"])
def open_spreadsheet():
    global sh
    received_data = request.get_json()
    gs_file = received_data['gs_file']

    try:
        sh = gc.open(gs_file)
    except gspread.SpreadsheetNotFound as e:
        return flask.jsonify({'msg':'Could not find the spreadsheet ' + gs_file, 'type':'error'})
    else:
        return flask.jsonify({'msg': 'Google spreadsheet ' + "{}".format(gs_file) + ' opened successfully', 'type':'info'})

@app.route('/getSpreadsheetID', methods=["GET"])
def get_spreadsheet_id():
    google_spreadsheet_url = ""
    try:
        google_spreadsheet_url = "https://docs.google.com/spreadsheets/d/%s" % sh.id
    except Exception as e:
        return flask.jsonify({'msg': f"An error occurred: {e}", 'type': 'error'})
    else:
        return flask.jsonify({'msg': 'Google spreadsheet created/updated here: ' + google_spreadsheet_url, 'type': 'info'})


@app.route('/delSpreadsheetByName', methods=["POST"])
def del_spreadsheet_by_name():
    global sh
    received_data = request.get_json()
    gs_file = received_data['gs_file']

    try:
        sh = gc.open(gs_file)
    except gspread.SpreadsheetNotFound as e:
        return flask.jsonify({'msg':'Could not find the spreadsheet ' + gs_file, 'type':'error'})
    else:
        try:
            gc.del_spreadsheet(sh.id)
        except Exception as e:
            return flask.jsonify({'msg': f"An error occurred: {e}", 'type':'error'})
        else:
            return flask.jsonify({'msg': 'Google spreadsheet ' + "{}".format(gs_file) + ' deleted', 'type':'info'})


@app.route('/shareSpreadsheet', methods=["GET"])
def share_spreadsheet():
    # global sh
    found_email = False
    try:
        # Try to get the email of the user to share the result with that account
        user_info = api_source.get('me').json()
        if 'email' in user_info and re.match(r"[^@]+@[^@]+\.[^@]+", user_info['email']):
            logger.info('Sharing with user email ' + user_info['email'])
            sh.share(user_info['email'], perm_type='user', role='writer')
            found_email = True
    except Exception as e:
        return flask.jsonify({'msg': f"An error occurred: {e}", 'type': 'error'})
    else:
        if found_email:
            return flask.jsonify(
                {'msg': 'Google spreadsheet shared successfully with ' + user_info['email'], 'type': 'info'})
        else:
            return flask.jsonify(
                {'msg': 'Sharing not possible: no email could be found for your user in the instance', 'type': 'warning'})

@app.route('/shareSpreadsheetWithEmail', methods=["POST"])
def share_spreadsheet_with_email():
    received_data = request.get_json()
    gs_file = received_data['gs_file']

    try:
        sh = gc.open(gs_file)
    except gspread.SpreadsheetNotFound as e:
        return flask.jsonify({'msg':'Could not find the spreadsheet ' + gs_file, 'type':'error'})
    else:
        try:
            sh.share(received_data['user_email'], perm_type='user', role='writer')
        except Exception as e:
            return flask.jsonify({'msg': f"An error occurred: {e}", 'type': 'error'})
        else:
            return flask.jsonify(
                    {'msg': 'Google spreadsheet shared successfully with ' + received_data['user_email'], 'type': 'info'})


@app.route('/importMetadata/<string:metadata_type_selection>', methods=["GET"])
def import_metadata(metadata_type_selection: str):

    metadata_types_supported = list()
    with open(app.config['CONFIG_FILE'], 'r') as f:
        for line in f:
            metadata_type = line.split(':')[0].strip()
            metadata_types_supported.append(metadata_type)

    preserve_metadata_fields_if_update = True
    print(metadata_type_selection)
    if '-json' in metadata_type_selection:
        filename_for_json_export = "metadata-all.json"
        if os.path.exists(filename_for_json_export):
            os.remove(filename_for_json_export)

        metadata_type_selection = metadata_type_selection.replace('-json', '')
        gen_json = True
    else:
        gen_json = False
    # global metadata_types_supported

    if metadata_type_selection != 'All':
        metadata_type_user_selection = [metadata_type_selection]
    else:
        metadata_type_user_selection = metadata_types_supported # All metadata supported
    # Expand pairs with +
    new_metadata_type_user_selection = list()
    for metadata_type in metadata_type_user_selection:
        if '+' in metadata_type:
            expanded_selection_list = metadata_type.split('+')
            new_metadata_type_user_selection.append(expanded_selection_list[0])
            new_metadata_type_user_selection.append(expanded_selection_list[1])
        else:
            new_metadata_type_user_selection.append(metadata_type)
    metadata_type_user_selection = new_metadata_type_user_selection


    # if args.user is not None and args.password is not None:
    #     api_source = Api(instance_url, args.user, args.password)
    # else:
    sheets_to_process = list()
    for ws in sh.worksheets():
        if ws.title in metadata_type_user_selection:
            sheets_to_process.append(ws.title)

        multilevel_identifiers = ['programStageDataElements', 'programTrackedEntityAttributes', 'dataSetElements', 'attributeValues']

    if len(sheets_to_process) == 0:
        return { 'msg': 'Metadata type not found in gspreadsheet, nothing to do', 'type':'warning'}

    for metadata_type in metadata_type_user_selection:

        if metadata_type in sheets_to_process:
            log_msg('** Processing ' + metadata_type)
            # Retain the original name for the metadata type, before removing spaces, etc...
            # Assuming there is only one multilevel
            identifier_name = ""
            df_multilevel_dict = {}
            metadata_type_selection = metadata_type

            # Load sheet/csv as dataframe and convert to json
            try:
                df = get_as_dataframe(sh.worksheet(metadata_type), evaluate_formulas=True, na_filter=False)
            except APIError as e:
                return flask.jsonify(
                    {'msg': 'gspread.exceptions.APIError: ' + "{}".format(str(e)), 'type': 'error'})
            #df = pd.read_excel(xls, sheet_name=metadata_type, na_filter=False)
            if df.shape[0] == 0 or (df['id'] == '').sum() == df.shape[0]:
                return {'msg':'GSpreadsheet is empty, nothing to do', 'type':'warning'}
            metadata_type = metadata_type.replace(' ', '')
            metadata_type = metadata_type[0].lower() + metadata_type[1:]
            if metadata_type.lower() == 'datasets':
                metadata_type = 'dataSets'

            # ---------------------
            #df = pd.read_csv(csv_file)
            df.replace('', np.nan, inplace=True)
            df = df.dropna(how='all')
            df = df.dropna(how='all', axis=1)
            # Replacement for dropna. We could also just convert '' to np.nan and call dropna
            # for column in df.columns:
            #     if (df[column].values == '').sum() == df.shape[0]:
            #         df.drop([column], axis=1, inplace=True)
            df.fillna('', inplace=True)
            # for bool_col in ['unique', 'mandatory', 'searchable', 'repeatable', 'compulsory', 'useCodeForOptionSet']:
            #     if bool_col in df.columns:
            #         df[bool_col] = df[bool_col].map({1.0: True, 0.0: False})
            if metadata_type in ['optionSets', 'legendSets']:
                _df = df.copy()
            column_index = 0
            for column in df.columns:
                if '[' in column and ']' in column:
                    # Add a tmp column
                    df.insert(column_index, 'tmp', ['']*df.shape[0])
                    indexes = df[df['id'] != ''].index.tolist()
                    # Append the last index
                    indexes.append(df.shape[0])
                    #indexes.append(df[df[column] != ''].index.tolist()[-1:][0]+1)
                    for i in range(0,len(indexes)-1):
                        # Slice column
                        column_list = df[column].loc[indexes[i]:indexes[i + 1] - 1].tolist()
                        if any(identifier in column for identifier in multilevel_identifiers):
                            # Multi level code
                            # Get the id, our anchor
                            id = df.at[indexes[i], 'id']
                            if id not in df_multilevel_dict:
                                df_multilevel_dict[id] = pd.DataFrame({})
                            df_multilevel_dict[id][column] = column_list
                            # Get the keyword
                            tmp = column.replace('[', '').replace(']', '').split('-')
                            if identifier_name == "":
                                identifier_name = tmp[0]
                        else:
                            # Otherwise expand into a list
                            # This call will fail if the column is not of type object
                            # Skip if all elements in list are empty
                            if not all(element == '' for element in column_list):
                                df.at[indexes[i], 'tmp'] = column_list

                if 'tmp' in df.columns:
                    # Drop the column and rename tmp
                    df.drop([column], axis=1, inplace=True)
                    df.rename(columns={"tmp": column}, inplace=True)

                column_index +=1

            # Rename column
            df.columns = df.columns.str.replace("[", "")
            df.columns = df.columns.str.replace("]", "")
            # Remove rows not given by index
            #df = df.drop(df.index[df[df['id'] == ''].index.tolist()])
            df['id'].replace('', np.nan, inplace=True)
            df.dropna(subset=['id'], inplace=True)
            # Remove multilevel columns, they will be processed later
            columns_to_drop = list()
            for column in df.columns:
                if any(identifier in column for identifier in multilevel_identifiers):
                    columns_to_drop.append(column)
            df = df.drop(columns_to_drop, axis=1)

            json_payload = df.to_dict(orient='records')
            index_elements_to_delete = list()
            index = 0
            for element in json_payload:
                keys_to_delete = list()
                for key in list(element):
                    if element[key] == "":
                        element.pop(key, None)
                    else:
                        if key.lower() == 'id' and 'DELETE' in element[key]:
                            index_elements_to_delete.append(index)
                        if '-' in key and key.lower() != 'id':
                            if key not in keys_to_delete:
                                keys_to_delete.append(key)
                            key_pairs = key.split('-')

                            # We are relying on id column to come first and informative ones after
                            if key_pairs[0] not in element:
                                if isinstance(element[key], list):
                                    # Store the lists which have been processed to make sure we don't overwrite
                                    element[key_pairs[0]] = list()
                                    for i in range(0, len(element[key])):
                                        element[key_pairs[0]].append({ key_pairs[1]: element[key][i] })
                                else:
                                    # We are relying on id column to come first and informative ones after
                                    element[key_pairs[0]] = dict()
                                    element[key_pairs[0]][key_pairs[1]] = element[key]
                            else:
                                # For Option Sets and Legend Sets we allow name to be there next to the id on a nested structure
                                if metadata_type not in ["optionSets", "legendSets"] and key_pairs[1] != 'name':  # name is informative
                                    if isinstance(element[key_pairs[0]], list):
                                        if len(element[key]) == len(element[key_pairs[0]]):
                                            for index in range(0, len(element[key])):
                                                element[key_pairs[0]][index][key_pairs[1]] = element[key][index]
                                    else:
                                        # For sharing-UserGroups
                                        if '{"' in element[key]:
                                            element[key_pairs[0]][key_pairs[1]] = json.loads(element[key])
                                        else:
                                            element[key_pairs[0]][key_pairs[1]] = element[key]

                # Remove the old keys
                for k in keys_to_delete:
                    element.pop(k, None)

                index += 1

            if metadata_type in ["optionSets", "legendSets"]:
                if metadata_type == "optionSets":
                    keyword_for_child = "options"
                elif metadata_type == "legendSets":
                    keyword_for_child = "legends"
                # Process options as well
                _df.columns = _df.columns.str.replace("[", "")
                _df.columns = _df.columns.str.replace("]", "")
                options = _df[_df.columns[pd.Series(_df.columns).str.startswith(keyword_for_child)]]
                options.columns = options.columns.str.replace(keyword_for_child + "-", "")
                json_options_payload = options.to_dict(orient='records')
                index_options_to_delete = list()
                index = 0
                for element in json_options_payload:
                    for key in list(element):
                        if key.lower() == 'id' and 'DELETE' in element[key]:
                            index_options_to_delete.append(index)
                    index += 1

            if bool(df_multilevel_dict):
                for id in df_multilevel_dict:
                    # add it to the payload
                    for i in range(0, len(json_payload)):
                        element = json_payload[i]
                        if 'id' in element and element['id'] == id:
                            json_payload[i] = {**json_payload[i],
                                            **extract_multi_level(df_multilevel_dict[id], identifier_name)}

            # We are going to consider that json export will only work with what exists on the file
            if not gen_json:
                json_payload = get_json_payload_to_instance(api_source, metadata_type, json_payload, index_elements_to_delete)
                if metadata_type == "optionSets":
                    json_payload = {**json_payload,  **get_json_payload_to_instance(api_source, 'options', json_options_payload, index_options_to_delete)}
            else:
                # The function get_json_payload_to_instance creates the key - list pair
                # Since we are skipping it in the previous step, we need to do it here
                json_payload = {metadata_type: json_payload}

            if metadata_type == "legendSets":
                # Not a great code here to assign legends to legendSets
                # Tried to reuse the code for options but it is not so straightforward
                # options can travel as their own json payload but legends don't have their own endpoint
                # so rather than adding them in the json, we need assign them one by one using id to their correspondent
                # legendSet object
                for i in range(0, len(json_payload['legendSets'])):
                    legendSet = json_payload['legendSets'][i]
                    for j in range(0, len(legendSet['legends'])):
                        legend = legendSet['legends'][j]
                        legend_id = legend['id']
                        for legend_counter in range(0, len(json_options_payload)):
                            if json_options_payload[legend_counter]['id'] == legend_id:
                                json_payload['legendSets'][i]['legends'][j] = json_options_payload[legend_counter]
                                break

            for element in json_payload[metadata_type]:
                for field in element:
                    if element[field] == "[]":
                        element[field] = list()
                    elif element[field] == "{}":
                        element[field] = dict()

            with open('metadata-'+metadata_type+'.json', 'w',
                      encoding='utf8') as file:
                file.write(json.dumps(json_payload, indent=4, sort_keys=True, ensure_ascii=False))
            file.close()

            if gen_json:
                try:
                    with open(filename_for_json_export, "r",encoding='utf8') as file:
                        json_file_all = json.load(file)
                except FileNotFoundError:
                    json_file_all = {}

                json_file_all.update(json_payload)

                with open(filename_for_json_export, 'w', encoding='utf8') as file:
                    file.write(json.dumps(json_file_all, indent=4, sort_keys=True, ensure_ascii=False))

            # Make sure metadata types which are linked by a + go together in the payload
            if metadata_type_selection not in metadata_types_supported:
                for meta_type in metadata_types_supported:
                    if metadata_type_selection in meta_type and '+' in meta_type:
                        metadata_type_together = meta_type.split('+')
                        if metadata_type_selection == metadata_type_together[0]:
                            all_json_payload = json_payload
                        else:
                            all_json_payload = {**json_payload, **all_json_payload}
                        if metadata_type_selection == metadata_type_together[-1]:
                            # If I use mergeMode=REPLACE -> It works only if the instance is empty, meaning that the metadata is being created for the first time.
                            # If I update the same metadata using mergeMode=REPLACE, the PRs are there but no PRAs (DHIS2 says that everything went ok though, no errors).
                            # If I use mergeMode=MERGE,  it does not work if the instance is empty, PRs are there but no PRAs show up in maintenance.
                            # If I import them again with mergeMode MERGE, then the PRs and PRAs are there. Again, DHIS2 does not raise any error
                            # Until I understand this mystery, I am doing two imports, first with REPLACE, then with MERGE
                            if preserve_metadata_fields_if_update:
                                all_json_payload = add_owned_fields_to_json_payload(api_source, all_json_payload)
                            # Do not update the server if we are just generating the json
                            if not gen_json:
                                result = post_to_server(api_source, all_json_payload, mergeMode='REPLACE')
                                result = post_to_server(api_source, all_json_payload, mergeMode='MERGE')
            else:
                # We are going to consider that json export will only work with what exists on the file
                if not gen_json:
                    if preserve_metadata_fields_if_update:
                        json_payload = add_owned_fields_to_json_payload(api_source, json_payload)
                    # Do not update the server if we are just generating the json
                    result = post_to_server(api_source, json_payload)

            if not gen_json and metadata_type == "categoryCombos":
                # Update the COCs
                try:
                    response = api_source.post('maintenance/categoryOptionComboUpdate')
                except RequestException as e:
                    # Print errors returned from DHIS2
                    result['type'] = 'error'
                    result['msg'] += "\nFailed to update COCs"
                    pass
                else:
                    result['type'] = 'info'
                    result['msg'] += "\nCOCs updated"

    if gen_json:
        result = dict()
        result['type'] = 'info'
        result['msg'] = "JSON file generated successfully"
        current_dir = os.getcwd()

    return flask.jsonify(result)


@app.route('/exportMetadata/<string:metadata_type_selection>', methods=["GET"])
def export_metadata(metadata_type_selection: str):

    generate_template = False
    result = dict()
    result['type'] = 'error'
    result['msg'] = 'Unknown error'

    metadata_types_supported = list()
    metadata_type_columns = dict()
    # Metadata supported comes from the conf file
    with open(app.config['CONFIG_FILE'], 'r') as f:
        for line in f:
            if len(line) > 0 and ':' in line:
                fields = line.strip().split(':')
                metadata_types_supported.append(fields[0])
                metadata_type_columns[fields[0]] = fields[1].replace(' ', '').strip().split(',')

    # This code is here in case we can do someday just one POST to update All
    # For the moment is useless, since the frontend must send individual requests for each metadata type
    if metadata_type_selection != 'All':
        metadata_type_user_selection = [metadata_type_selection]
    else:
        metadata_type_user_selection = metadata_types_supported # All metadata supported

    current_worksheet_names = [worksheet.title for worksheet in sh.worksheets()]

    logger.info('Pulling configuration from metadata schemas')
    mandatory_fields = dict()
    df_conf = pd.DataFrame()
    for metadata_type in metadata_type_columns:
        if metadata_type in metadata_type_user_selection:
            df_conf, mandatory_fields = add_constant_schemas_to_configuration(api_source, metadata_type, df_conf, mandatory_fields)

    for metadata_type in metadata_type_user_selection:
        logger.info('Processing ' + metadata_type)

        if not generate_template:
            metadata_columns = metadata_type_columns[metadata_type]
            # Build fields
            fields = metadata_columns.copy()
            subfields = dict()
            subsubfields = dict()
            api_fields = list()
            for i in range(0, len(fields)):
                column = fields[i].replace('[', '').replace(']', '')
                if '-' in column:
                    s = column.split('-')
                    if len(s) == 2:
                        if s[0] not in subfields:
                            subfields[s[0]] = list()
                        subfields[s[0]].append(s[1])
                    elif len(s) == 3:
                        if s[0] not in subfields:
                            subfields[s[0]] = list()
                        if s[1] not in subsubfields:
                            subsubfields[s[1]] = list()
                        subsubfields[s[1]].append(s[2])

                    if len(s) == 3 and (i == len(fields)-1 or '-' + s[1] + '-' not in fields[i+1]):
                        subfields[s[0]].append(s[1]+'['+','.join(subsubfields[s[1]])+']')

                else:
                    api_fields.append(column)
            for key in subfields:
                if isinstance(subfields[key], list):
                    api_fields.append(key+'['+','.join(subfields[key])+']')

            fields = ','.join(api_fields)

            df = pd.DataFrame({}, columns=metadata_columns)

            api_endpoint = metadata_type.strip().replace(' ', '')
            api_endpoint = api_endpoint[0].lower() + api_endpoint[1:]

            # We can add filters in the future, for example to get only GEN Library
            filter = ""
            params = {  "paging": "false",
                        "fields": fields
                    }

            if filter != "":
                params['filter'] = filter

            metadata = api_source.get(api_endpoint,
                          params=params).json()[api_endpoint]

            if len(metadata) == 0:
                logger.info('   Nothing found')
                result['type'] = 'warning'
                result['msg'] = 'Nothing found'
                continue
            else:
                logger.info('   Found ' + str(len(metadata)) + ' elements')
                result['type'] = 'info'
                result['msg'] = 'Found ' + str(len(metadata)) + ' elements'

            for metaobject in metadata:
                new_row = dict.fromkeys(metadata_columns, '')
                new_row_list = list()
                for column in metadata_columns:
                    if column in metaobject:
                        new_row[column] = metaobject[column]
                    elif '[' in column:
                        keys = column.replace('[', '').replace(']', '').split('-')
                        if keys[0] in metaobject and isinstance(metaobject[keys[0]], list):
                            if len(keys) == 2:
                                for i in range(0, len(metaobject[keys[0]])):
                                    v = metaobject[keys[0]][i]
                                    # We capture here a possible error when an Option Set has None options which
                                    # makes the app crash
                                    if v == None:
                                        result['type'] = 'error'
                                        if 'name' in metaobject:
                                            result['msg'] = 'Metadata object ' + metaobject['name'] + ' has None values'
                                        else:
                                            result['msg'] = 'Metadata object has None values'
                                        return flask.jsonify(result)
                                    if keys[1] in v:
                                        if i == 0:
                                            new_row[column] = v[keys[1]]
                                        else:
                                            if len(new_row_list) < i:
                                                new_row_list.append(dict.fromkeys(metadata_columns, ''))
                                            new_row_list[(i - 1)][column] = v[keys[1]]
                            elif len(keys) == 3:
                                for i in range(0, len(metaobject[keys[0]])):
                                    v = metaobject[keys[0]][i]
                                    if keys[1] in v and keys[2] in v[keys[1]]:
                                        if i == 0:
                                            new_row[column] = v[keys[1]][keys[2]]
                                        else:
                                            if len(new_row_list) < i:
                                                new_row_list.append(dict.fromkeys(metadata_columns, ''))
                                            new_row_list[(i - 1)][column] = v[keys[1]][keys[2]]

                    else:
                        keys = column.split('-')
                        if len(keys) == 2 and keys[0] in metaobject:
                            if keys[1] in metaobject[keys[0]]:
                                new_row[column] = metaobject[keys[0]][keys[1]]
                                if type(new_row[column]) == dict:
                                    new_row[column] = json.dumps(new_row[column]).replace("},", "},\n")
                            # else:
                            #     if 'id' in metaobject[keys[0]]:
                            #         metadata_field = api_source.get(keys[0]+'s'+'/' + metaobject[keys[0]]['id'],
                            #                              params={"paging": "false",
                            #                                      "fields": keys[1]}).json()
                            #         new_row[column] = metadata_field[keys[1]]

                new_row_df = pd.DataFrame([new_row], columns=df.columns)
                # Match the data types of new_row_df to df
                for column in new_row_df.columns:
                    if column in df:
                        new_row_df[column] = new_row_df[column].astype(df[column].dtype)

                # Function to convert all object columns with all-bool values to bool dtype
                def convert_bool_columns(df):
                    for col in df.columns:
                        if df[col].dtype == 'object' and all(df[col].dropna().apply(lambda x: isinstance(x, bool))):
                            df[col] = df[col].astype(bool)
                    return df

                # Convert bool columns for both DataFrames
                df = convert_bool_columns(df)
                new_row_df = convert_bool_columns(new_row_df)

                # Concatenate the DataFrames
                df = pd.concat([df, new_row_df], ignore_index=True)

                if len(new_row_list) > 0:
                    for new_row in new_row_list:
                        new_row_df = pd.DataFrame([new_row], columns=df.columns)
                        df = pd.concat([df, new_row_df], ignore_index=True)

            if metadata_type not in current_worksheet_names:
                # When we create a spreadsheet it cannot be empty, so Sheet1 is created
                # automatically. If it is still there, we can reuse it for the new worksheet
                if 'Sheet1' in current_worksheet_names:
                    ws = sh.sheet1
                    ws.update_title(metadata_type)
                    current_worksheet_names.remove('Sheet1')
                else:
                    max_retries = 5
                    retries = 0
                    while True:
                        try:
                            ws = sh.add_worksheet(title=metadata_type, rows=df.shape[0], cols=df.shape[1])
                        except gspread.exceptions.APIError as e:
                            time.sleep(5)
                            if retries < max_retries:
                                retries += 1
                            else:
                                result['type'] = 'error'
                                result['msg'] = str(e)
                                return flask.jsonify(result)
                            pass
                        else:
                            break
                # Update current worksheets in the spreadsheet
                current_worksheet_names.append(metadata_type)
            else:
                while True:
                    try:
                        ws = sh.worksheet(metadata_type)
                    except gspread.exceptions.APIError as e:
                        time.sleep(30)
                        pass
                    else:
                        break

            # We need to add an ' if the text starts with +, otherwise it is interpreted as a formula
            # and we get parsing error in the spreadsheet
            # However, if we add one ', we end up with '' in the cell value.
            # The reason for this cell is because the first apostrophe is added by the applymap() method in the Python code,
            # and the second apostrophe is added by Google Sheets to indicate that the cell contains text.
            # Unfortunately, replacing '' with ' those not work either. So we need to add a placeholder APOSTROPHE
            # which then gets replaced later on in Adding Formatting stage
            df = df.applymap(lambda x: "APOSTROPHE" + x if isinstance(x, str) and x.startswith("+") else x)
            # Add some empty rows at the end
            current_number_rows = df.shape[0]
            columns = df.columns
            # Create a DataFrame containing some empty rows
            empty_df = pd.DataFrame(index=range(int(current_number_rows/4)), columns=columns)
            df = pd.concat([df, empty_df], ignore_index=True)

            while True:
                try:
                    set_with_dataframe(worksheet=ws, dataframe=df, include_index=False,
                                       include_column_header=True, resize=True)
                except gspread.exceptions.APIError as e:
                    time.sleep(30)
                    pass
                else:
                    break

        else:
            logger.info('Adding worksheet as an empty template')
            result['type'] = 'info'
            result['msg'] += 'Adding worksheet as an empty template'
            metadata_type_ws_exists = True
            try:
                sh.worksheet(metadata_type)
            except gspread.WorksheetNotFound:
                metadata_type_ws_exists = False
            if not metadata_type_ws_exists:
                logger.info('Adding ' + metadata_type)
                metadata_columns = metadata_type_columns[metadata_type]
                df = pd.DataFrame(columns=metadata_columns, index=range(100))
                df = df.fillna('')
                while True:
                    try:
                        ws = sh.add_worksheet(title=metadata_type, rows=df.shape[0], cols=df.shape[1])
                        set_with_dataframe(worksheet=ws, dataframe=df, include_index=False,
                                           include_column_header=True, resize=True)
                    except Exception as e:
                        logger.error('Quota exceeded')
                        logger.error(str(e))
                        time.sleep(30)
                        pass
                    else:
                        break

        logger.info('Adding formatting')
        requests = apply_formatting_to_worksheet(ws, metadata_types_supported, current_worksheet_names, df_conf, mandatory_fields[metadata_type])
        # Apply the requests using batch updates
        while True:
            try:
                sh.batch_update({"requests": requests})
            except gspread.exceptions.APIError as e:
                if "'code': 400" in str(e) or "'code': 500" in str(e):
                    for request in requests:
                        try:
                            sh.batch_update({"requests": [request]})
                        except googleapiclient.errors.HttpError as e:
                            # Check if the error is due to the row size issue
                            if e.resp.status == 400 and 'beyond the last requested row' in str(e):
                                pass
                        except gspread.exceptions.APIError as e:
                            print(str(e))
                            # print('IN THIS REQUEST')
                            # print(request)
                            pass
                        # else:
                        #     print('OK')
                        #     pprint.pprint(request)
                    break
                time.sleep(10)
                pass
            else:
                break

    return flask.jsonify(result)


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-c', '-conf', help='Custom metadata conf file (optional), metadata_types.conf is used by default')
    parser.add_argument('-a', '-auth', required=True, help='Google API Key (mandatory)')
    args = parser.parse_args()

    config_file = args.c if args.c else 'metadata_types.conf'
    auth_file = args.a

    if not auth_file:
        print('Warning: No Google API Key provided. Please generate one using this link: https://support.google.com/googleapi/answer/6158862?hl=en')
    
    gc = authorize_google_sheets(auth_file)

    app = create_app(config_file)
    app.run()
