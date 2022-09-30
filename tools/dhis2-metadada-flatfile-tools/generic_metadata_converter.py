import json
import chardet
import pandas as pd
import sys
import numpy as np
from dhis2 import RequestException, Api, setup_logger, logger
from tools.dhis2 import post_to_server
from urllib.request import urlopen
import argparse
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from gspread_formatting import *
from gspread.exceptions import APIError


def read_metadata_types_conf_file(filename):
    with open(filename) as file:
        metadata_type_columns = dict()
        for line in file:
            # metadata_type:columns separated by commas
            fields = line.split(':')
            metadata_type_columns[fields[0]] = fields[1].replace(' ', '').strip().split(',')
    return metadata_type_columns


def main():

    if len(sys.argv) != 4:
        print('3 arguments required: 1. Name of the spreadsheet which will be created/updated 2. Instance url to extract from 3. Configuration file')
        exit(1)
    package_name = sys.argv[1]
    instance_url = sys.argv[2]
    conf_file = sys.argv[3]

    credentials_file = 'auth.json'
    try:
        f = open(credentials_file)
    except IOError:
        print("Please provide file auth.json with credentials for DHIS2 server")
        exit(1)
    else:
        with open(credentials_file, 'r') as json_file:
            credentials = json.load(json_file)
        logger.info('Connected to API in ' + instance_url + ' as user: ' + credentials['dhis']['username'])
        api_source = Api(instance_url, credentials['dhis']['username'], credentials['dhis']['password'])
    # package_file = sys.argv[1]
    # enc = chardet.detect(open(package_file, 'rb').read())['encoding']
    # with open(package_file, 'r', encoding=enc) as json_file:
    #     package_metadata = json.load(json_file)

    df = dict()
    metadata_type_columns = read_metadata_types_conf_file(conf_file)

    api_filters = dict()
    api_filters['dataElements'] = "name:like:GEN"
    api_filters['trackedEntityAttributes'] = "name:like:GEN"
    api_filters['optionSets'] = "name:like:GEN"

    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    google_spreadshseet_credentials = 'dummy-data-297922-97b90db83bdc.json'

    sh_name = package_name
    try:
        f = open(google_spreadshseet_credentials)
    except IOError:
        print("Please provide file with google spreadsheet credentials")
        exit(1)
    else:
        credentials = ServiceAccountCredentials.from_json_keyfile_name(google_spreadshseet_credentials, scope)

    gc = gspread.authorize(credentials)
    mode='update'
    sheet1_still_there = False
    try:
        gs = gc.open(sh_name)
    except gspread.SpreadsheetNotFound:
        mode='create'
        sheet1_still_there = True
        gs = gc.create(sh_name)
        pass
    gs.share('manuel@dhis2.org', perm_type='user', role='writer')

    metadata_type_supported = metadata_type_columns.keys()

    # package_metadata_types = package_metadata.keys()

    for metadata_type in metadata_type_supported: #package_metadata_types:
        if metadata_type != 'Attributes':
            continue

        if metadata_type in metadata_type_supported:
            logger.info('Processing ' + metadata_type)

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
            logger.info(api_endpoint + '?' + 'fields=' + fields)

            metadata = api_source.get(api_endpoint,
                          params={"paging": "false",
                                  #"filter": api_filters[metadata_type],
                                  "fields": fields
                                  }).json()[api_endpoint]
            # metadata = package_file[metadata_type]

            if len(metadata) == 0:
                logger.info('   Nothing found')
                continue
            else:
                logger.info('   Found ' + str(len(metadata)) + ' elements')

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
                            # else:
                            #     if 'id' in metaobject[keys[0]]:
                            #         metadata_field = api_source.get(keys[0]+'s'+'/' + metaobject[keys[0]]['id'],
                            #                              params={"paging": "false",
                            #                                      "fields": keys[1]}).json()
                            #         new_row[column] = metadata_field[keys[1]]

                df = df.append(new_row, ignore_index=True)
                if len(new_row_list) > 0:
                    for new_row in new_row_list:
                        df = df.append(new_row, ignore_index=True)

            metadata_type_ws_exists = True
            try:
                gs.worksheet(metadata_type)
            except gspread.WorksheetNotFound:
                metadata_type_ws_exists = False

            if mode == 'create' or not metadata_type_ws_exists:
                if sheet1_still_there:
                    ws = gs.sheet1
                    ws.update_title(metadata_type)
                    sheet1_still_there = False
                else:
                    ws = gs.add_worksheet(title=metadata_type, rows=df.shape[0], cols=df.shape[1])
            else:
                ws = gs.worksheet(metadata_type)

            ws.clear()
            set_with_dataframe(worksheet=ws, dataframe=df, include_index=False,
                               include_column_header=True, resize=True)
            ws.format('A1:' + (chr (ord ('A') + df.shape[1] - 1)) + '1', {'textFormat': {'bold': True}})
            set_frozen(ws, rows=1)
            time.sleep(5)

    google_spreadsheet_url = "https://docs.google.com/spreadsheets/d/%s" % gs.id
    logger.info('Google spreadsheet created/updated here: ' + google_spreadsheet_url)



if __name__ == "__main__":
    main()
