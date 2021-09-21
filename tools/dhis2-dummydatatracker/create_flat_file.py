from dhis2 import Api, RequestException, is_valid_uid
import logzero
from logzero import logger
import sys
import pandas as pd
from tools.json import reindex, json_extract, json_extract_nested_ids
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from gspread_formatting import *
import re


try:
    f = open("./auth.json")
except IOError:
    print("Please provide file auth.json with credentials for DHIS2 server")
    exit(1)
else:
    api_source = Api.from_auth_file('./auth.json')

# If no file path is specified, it tries to find a file called dish.json in:
#
# the DHIS_HOME environment variable
# your Home folder


# setup the logger
log_file = "./dummyDataTracker.log"
logzero.logfile(log_file)


def add_repeatable_stages(df, stage_counter):
    if df['Stage'].isna().sum() > 0:
        stage_indexes = df.index[df['Stage'].notnull()].tolist()
    else:
        stage_indexes = df.index[(df.Stage != '')].tolist()
    list_df = list()
    for i in range(0, len(stage_indexes)):
        if (i + 1) != len(stage_indexes):
            df_event = df[stage_indexes[i]:(stage_indexes[i + 1])]
        else:
            df_event = df[stage_indexes[i]:]
        # It is a stage
        if i != 0:
            stage_uid = df_event.iloc[0]['UID']
            if stage_uid not in stage_counter:
                stage_counter[stage_uid] = 1  # At least once
                logger.warning("Not repeating stage uid " + stage_uid)
            if stage_counter[stage_uid] > 1:
                for j in range(0, stage_counter[stage_uid]):
                    new_df_slice = df_event.copy()
                    # new_df_slice.at[new_df_slice.index[0], 'UID'] = stage_uid + '_' + str(j)
                    list_df.append(new_df_slice)
            else:
                list_df.append(df_event.copy())
        else:
            list_df.append(df_event.copy())

    return pd.concat(list_df).reset_index(drop=True)


def add_json_tei_to_metadata_df(json_tei, df):
    def set_value(df, uid, value, min_pos=0):
        positions = df.index[(df.UID == uid) & (df.value == '')].tolist()
        # The idea with min_pos is to avoid filling data elements in the wrong stage
        # if a DE has a value in the next repeatable stage but it wasn't filled in the current one,
        # when we start filling the next stage we risk filling it in the previous one (because
        # it satisfies (df.UID == uid) & (df.value == '')). With min_pos we tell the script
        # start considering indexes starting from a certain value (the position of eventDate, the first DE which
        # is always present for the stage

        # Note: Packages like DRS use the same DE in different Program Stages. We need to verify that this works with
        # that use case
        if min_pos > 0:
            positions = [x for x in positions if x >= min_pos]
        if len(positions) == 0:
            # logger.error("Dataframe has not sufficient stages to fill datalement " + uid)
            return -1
        else:
            df.at[positions[0], 'value'] = value
            return positions[0]

    # program UID is in the first row in Stage Enrollment
    program_id = df.iloc[0]['UID']
    list_of_UIDs = df['UID'].tolist()
    # df_uid = df.set_index('UID')
    column = 'TEI_' + json_tei['trackedEntityInstance']
    df['value'] = ""  # np.nan
    # We are assuming just one enrollment in the program
    if len(json_tei['enrollments']) == 1 and json_tei['enrollments'][0]['program'] == program_id:
        json_enrollment = json_tei['enrollments'][0]
        # json_extract returns a list of values. It should be just one value in the list, so we get element 0
        # dates are in the format 2020-11-05T00:00:00.000, so we truncate them
        set_value(df, program_id, json_extract(json_enrollment, 'enrollmentDate')[0][0:10])
        for attribute in json_tei["attributes"]:
            if attribute["attribute"] not in list_of_UIDs:
                logger.error('Attribute = ' + attribute["attribute"] + ' in TEI = ' + json_tei[
                    'trackedEntityInstance'] + ' not present in df')
                return False
            set_value(df, attribute["attribute"], attribute["value"])

        json_events = json_enrollment["events"]
        pos = dict()
        for event in json_events:
            # Considering here that program stages appear in order but it might be better to loop through them in order
            program_stage_uid = event['programStage']
            # if the programme allows for the future scheduling of events,
            # this will mean that even though the event date is mandatory,
            # scheduled events which have not yet happen, will not yet have an event date
            if 'eventDate' in event:
                pos[program_stage_uid] = set_value(df, program_stage_uid, event['eventDate'][0:10])
            else:
                pos[program_stage_uid] = set_value(df, program_stage_uid, '')
            if pos == -1:  # There was a problem
                return False
            if 'dataValues' in event:
                for dataValue in event['dataValues']:
                    if dataValue["dataElement"] not in list_of_UIDs:
                        logger.error('Data Element = ' + dataValue["dataElement"] + ' in TEI = ' + json_tei[
                            'trackedEntityInstance'] + ' not present in df')
                    else:
                        result = set_value(df, dataValue["dataElement"], dataValue["value"], pos[program_stage_uid])
                    if result == -1:
                        # Check that the DE is assigned to the proram stage
                        program_stage_info = api_source.get('programStages/' + program_stage_uid,
                                                            params={
                                                                "fields": "programStageDataElements[dataElement]"}).json()
                        data_elements_in_ps = json_extract_nested_ids(program_stage_info, 'dataElement')
                        if dataValue["dataElement"] not in data_elements_in_ps:
                            logger.error("TEI " + json_tei['trackedEntityInstance'] +
                                         " has a dataValue for DE " + dataValue["dataElement"] +
                                         " in stage " + program_stage_uid +
                                         " but this DE is NOT assigned to this PS")
                        else:
                            logger.error("Dataframe has not sufficient stages to fill datalement "
                                         + dataValue["dataElement"])

    else:
        if len(json_tei['enrollments']) > 1:
            logger.error('Multi-enrollments not supported')
            return False
        else:
            logger.error('TEI does not belong to the dataframe program')
            return False

    # Rename column
    df.rename(columns={"value": 'TEI_' + json_tei['trackedEntityInstance']}, inplace=True)
    return True


def create_google_spreadsheet(program, df, share_with):
    params_data = {'PARAMETER': ['program_uid', 'metadata_version', 'server_url', 'orgUnit_uid', 'orgUnit_level',
                                 'ignore_validation_errors', 'start_date', 'end_date', 'chunk_size'],
                   'VALUE': [ program['id'], program['version'], '', '', 4, 'FALSE', '', '', 50],
                   'NOTE': ['', 'Metadata version for this program', 'E.g. https://who-dev.dhis2.org/dev',
                            'if empty, uses all org units assigned to the program',
                            'default = 4, facility', 'true/false', 'dates in the form YYYY-MM-DD', 'default = today',
                            'maximum number of TEIs to include in the payload when POST to server']}
    df_params = pd.DataFrame(params_data)
    number_replicas_data = {'PRIMAL_ID': ['TEI_1', 'TEI_2', 'TEI_3', 'TEI_4', 'TEI_5'],
                            'NUMBER': ['50', '50', '50', '50', '50']}
    df_number_replicas = pd.DataFrame(number_replicas_data)
    sh_name = program['name']
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

    try:
        gc = gspread.authorize(credentials)
        mode='update'
        try:
            sh = gc.open(sh_name)
        except gspread.SpreadsheetNotFound:
            mode='create'
            sh = gc.create(sh_name)
            pass
        sh.share('manuel@dhis2.org', perm_type='user', role='writer')
        #sh.share('yury@dhis2.org', perm_type='user', role='writer')
        #sh.share('enzo@dhis2.org', perm_type='user', role='writer')
        if share_with is not None:
            for email in share_with:
                sh.share(email[0], perm_type='user', role='writer')
        if mode == 'create' or not sh.worksheet('DUMMY_DATA'):
            wks_dd = sh.sheet1
            wks_dd.update_title('DUMMY_DATA')
        else:
            wks_dd = sh.worksheet('DUMMY_DATA')
        if mode == 'create' or not sh.worksheet('PARAMETERS'):
            wks_params = sh.add_worksheet(title="PARAMETERS", rows=df_params.shape[0], cols=df_params.shape[1])
        else:
            wks_params = sh.worksheet('PARAMETERS')
        if mode == 'create' or not sh.worksheet('NUMBER_REPLICAS'):
            wks_number_replicas = sh.add_worksheet(title="NUMBER_REPLICAS", rows=df_number_replicas.shape[0],
                                                   cols=df_number_replicas.shape[1])
        else:
            wks_number_replicas = sh.worksheet('NUMBER_REPLICAS')
        tmp_df = df.copy()
        if mode == 'create':
            for tei_col in range(1, 6):
                tmp_df['TEI_' + str(tei_col)] = ''
        set_with_dataframe(wks_dd, tmp_df)
        # wks_dd.add_protected_range('A1:G'+str(df.shape[0]+2))
        wks_dd.freeze(cols=7)
        del tmp_df
        # wks_params = sh.add_worksheet(title="PARAMETERS", rows=df_params.shape[0], cols=df_params.shape[1])
        # wks_dd.add_protected_range('B2:B3')
        if mode == 'create':
            set_with_dataframe(wks_params, df_params)
            set_column_widths(wks_params, [('A', 200), ('B:', 100), ('C:', 600)])
            # wks_number_replicas = sh.add_worksheet(title="NUMBER_REPLICAS", rows=df_number_replicas.shape[0],
            #                                        cols=df_number_replicas.shape[1])
            set_with_dataframe(wks_number_replicas, df_number_replicas)
            set_column_widths(wks_number_replicas, [('A', 100), ('B:', 100)])
        # Add conditional format. Mandatory column in G position = TRUE should have bold text
        rule = ConditionalFormatRule(
            ranges=[GridRange.from_a1_range('G1:G2000', wks_dd)],
            booleanRule=BooleanRule(
                condition=BooleanCondition('TEXT_EQ', ['TRUE']),
                format=CellFormat(textFormat=TextFormat(bold=True))
            )
        )
        rules = get_conditional_format_rules(wks_dd)
        # rules.clear()
        rules.append(rule)
        rules.save()

        batch = batch_updater(sh)
        # Add header formatting
        header = chr(65) + str(1) + ':' + chr(65 + df.shape[1] - 1) + str(1)
        batch.format_cell_range(wks_dd, header, CellFormat(
            backgroundColor=Color(0.40, 0.65, 1),
            textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1), fontSize=11),
            horizontalAlignment='CENTER'
        ))
        # Added alternative formatting
        for i in range(3, df.shape[0], 2):
            even_row = chr(65) + str(i) + ':' + chr(65 + df.shape[1] - 1) + str(i)
            batch.format_cell_range(wks_dd, even_row, CellFormat(
                backgroundColor=Color(0.90, 0.95, 1)
            ))
        b = Border("SOLID_THICK", Color(0, 0, 0))
        # Add border to the stages
        stage_indexes = df.index[df['Stage'] != ''].tolist()
        for i in stage_indexes:
            stage_row = chr(65) + str(i + 2) + ':' + chr(65 + df.shape[1] - 1) + str(i + 2)
            batch.format_cell_range(wks_dd, stage_row, CellFormat(borders=Borders(top=b)))
        # Add formatting to spreadsheet
        batch.execute()

    except Exception as e:
        logger.error(str(e))
        return ""
    else:
        spreadsheet_url = "https://docs.google.com/spreadsheets/d/%s" % sh.id
        return spreadsheet_url


def main():
    pd.set_option('display.max_columns', None)

    import argparse

    my_parser = argparse.ArgumentParser(prog='create_flat_file',
                                        description='Create dummy data flat file in Google Spreadsheets',
                                        epilog="python create_flat_file Lt6P15ps7f6 --with_teis_from=GZ5Ty90HtW --share_with=johndoe@dhis2.org"
                                               "\npython create_flat_file Lt6P15ps7f6 --repeat_stage Hj38Uhfo012 5 --repeat_stage 77Ujkfoi9kG 3 --share_with=person1@dhis2.org --share_with=person2@dhis2.org",
                                        formatter_class=argparse.RawDescriptionHelpFormatter)
    my_parser.add_argument('Program_UID', metavar='program_uid', type=str,
                           help='the uid of the program to use')
    my_parser.add_argument('-wtf', '--with_teis_from', action="store", dest="OrgUnit", type=str,
                           help='Pulls TEIs from specified org unit and adds them to flat file. '
                                'Eg: --with_teis_from_ou=Q7RbNZcHrQ9')
    my_parser.add_argument('-rs', '--repeat_stage', action="append", metavar=('stage_uid', 'number_repeats'), nargs=2,
                           help='provide a stage uid which is REPEATABLE and specify how many times you are planning to enter it. '
                                'Eg: --repeat_stage QXtjg5dh34A 3')
    my_parser.add_argument('-sw', '--share_with', action="append", metavar='email', nargs=1,
                           help='email address to share the generated spreadsheet with as OWNER. '
                                'Eg: --share_with=peter@dhis2.org')
    args = my_parser.parse_args()

    program_uid = args.Program_UID
    if not is_valid_uid(program_uid):
        print('The program uid specified is not valid')
        sys.exit()
    if args.OrgUnit is not None and not is_valid_uid(args.OrgUnit):
        print('The orgunit uid specified is not valid')
        sys.exit()
    if args.repeat_stage is not None and len(args.repeat_stage) > 0:
        for param in args.repeat_stage:
            if not is_valid_uid(param[0]):
                print('The program stage uid specified ' + param[0] + ' is not valid')
                sys.exit()
            try:
                int(param[1])
            except ValueError:
                print('The repetition value ' + param[1] + ' is not an integer')
                sys.exit()
    if args.share_with is not None and len(args.share_with) > 0:
        for param in args.share_with:
            if not (re.search('^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$', param[0])):
                print("The email address " + param[0] + " is not valid")

    # Print DHIS2 Info
    logger.warning("Server source running DHIS2 version {} revision {}"
                   .format(api_source.version, api_source.revision))

    ##############
    # df = pd.read_csv('program-Case_Based_Surveillance.csv', sep=None, engine='python')
    # #
    # # # stages_counter = { 'K5ac7u3V5bB': 1, 'ang4CLldbIu': 5, 'UvYb6qJpQu0': 1 }
    # #
    # # #json_tei = api_source.get('trackedEntityInstances/dRdztYSReOZ', params={'fields':'*'}).json()
    # #
    # params = {
    #     'ou': 'RI95HQRHbKc', # GD7TowwI46c
    #     'ouMode': 'DESCENDANTS',
    #     'program': program_uid,
    #     'skipPaging': 'true',
    #     'lastUpdatedDuration': '4d',
    #     'fields': '*',
    #     'includeAllAttributes': 'true'
    # }
    #
    # list_teis = api_source.get('trackedEntityInstances', params=params).json()['trackedEntityInstances']
    #
    # logger.info("Found " + str(len(list_teis)) + " TEIs")
    #
    # user = 'robot'
    # stages_counter = dict()
    # for tei in list_teis:
    #     counter = dict()
    #     if "enrollments" in tei and len(tei["enrollments"][0]) > 0: # and tei["enrollments"][0]["storedBy"] == user:
    #         if len(tei['enrollments']) == 1:
    #             if tei['enrollments'][0]['program'] == program_uid:
    #                 if 'events' in tei['enrollments'][0]:
    #                     events = tei['enrollments'][0]['events']
    #                     for event in events:
    #                         if event["programStage"] in counter:
    #                             counter[event["programStage"]] +=1
    #                         else:
    #                             counter[event["programStage"]] = 1
    #             else:
    #                 logger.error("TEI enrolled in program " + tei['enrollments'][0]['program'] + " not supported")
    #         else:
    #             logger.error('error, multi-enrollment not supported')
    #     for key in counter:
    #         if key not in stages_counter or stages_counter[key] < counter[key]:
    #             stages_counter[key] = counter[key]
    #             logger.info('Found ' + str(stages_counter[key]) + ' instances of ' + key)
    #
    # df = add_repeatable_stages(df, stages_counter)
    # for tei in list_teis:
    #     # if tei['trackedEntityInstance'] != 'j17HROzXGEn':
    #     #     continue
    #     if len(tei["enrollments"][0]) > 0:  # and tei["enrollments"][0]["storedBy"] == user:
    #         result = add_json_tei_to_metadata_df(tei, df)

    # export_csv = df.to_csv(r'./program-Case_Based_Surveillance-Dummy_data.csv', index=None, header=True)

    ###########
    df = pd.DataFrame({}, columns=["Stage", "Section", "TEA / DE / eventDate", "UID", "valueType", "optionSet",
                                   "mandatory"])

    try:
        program = api_source.get('programs/' + program_uid,
                                 params={"paging": "false",
                                         "fields": "id,name,enrollmentDateLabel,programTrackedEntityAttributes,programStages,programRuleVariables,organisationUnits,trackedEntityType,version"}).json()
    except RequestException as e:
        if e.code == 404:
            logger.error('Program ' + program_uid + ' specified does not exist')
            sys.exit()

    if isinstance(program, dict):
        # If the program has many org units assigned, this can take a long time to run!!!
        # orgunits_uid = json_extract_nested_ids(program, 'organisationUnits')
        # if args.OrgUnit is not None and args.OrgUnit not in orgunits_uid:
        #     logger.error('The organisation unit ' + args.OrgUnit + ' is not assigned to program ' + program_uid)
        # print('Number of OrgUnits:' + str(len(orgunits_uid)))

        programStages_uid = json_extract_nested_ids(program, 'programStages')
        if args.repeat_stage is not None:
            for param in args.repeat_stage:
                found = False
                for uid in programStages_uid:
                    if param[0] == uid:
                        found = True
                        break
                if not found:
                    logger.error(uid + ' specified is not a valid stage for program ' + program_uid)
                    sys.exit()

        teas_uid = json_extract_nested_ids(program, 'trackedEntityAttribute')
        programRuleVariables_uid = json_extract_nested_ids(program, 'programRuleVariables')

        print('Program:' + program['name'])

        print('Number of TEAs:' + str(len(teas_uid)))
        TEAs = api_source.get('trackedEntityAttributes',
                              params={"paging": "false", "fields": "id,name,aggregationType,valueType,optionSet",
                                      "filter": "id:in:[" + ','.join(teas_uid) + "]"}).json()[
            'trackedEntityAttributes']
        TEAs = reindex(TEAs, 'id')

        # Add the first row with eventDate and Enrollment label
        enrollmentDateLabel = "Enrollment date"
        if 'enrollmentDateLabel' in program:
            enrollmentDateLabel = program['enrollmentDateLabel']
        # Add the program UID as UID for enrollmentDate
        df = df.append({"Stage": "Enrollment", "Section": "", "TEA / DE / eventDate": enrollmentDateLabel,
                        "UID": program_uid, "valueType": "DATE", "optionSet": "", "mandatory": 'True'},
                       ignore_index=True)
        optionSetDict = dict()
        for TEA in program['programTrackedEntityAttributes']:
            tea_uid = TEA['trackedEntityAttribute']['id']
            optionSet_def = ""
            if 'optionSet' in TEAs[tea_uid]:
                optionSet = TEAs[tea_uid]['optionSet']['id']
                if optionSet not in optionSetDict:
                    options = api_source.get('options', params={"paging": "false",
                                                                "order": "sortOrder:asc",
                                                                "fields": "id,code",
                                                                "filter": "optionSet.id:eq:" + optionSet}).json()[
                        'options']
                    optionsList = json_extract(options, 'code')
                    optionSetDict[optionSet] = optionsList
                optionSet_def = '\n'.join(optionSetDict[optionSet])
            df = df.append({"Stage": "", "Section": "", "TEA / DE / eventDate": TEA['name'],
                            "UID": tea_uid,
                            "valueType": TEA['valueType'], "optionSet": optionSet_def,
                            "mandatory": TEA['mandatory']}, ignore_index=True)

            # print("TEA: " + TEA['name'] + " (" + TEA['valueType'] + ")")

        print('Number of Program Rule Variables:' + str(len(programRuleVariables_uid)))
        programRuleVariables = api_source.get('programRuleVariables',
                                              params={"paging": "false",
                                                      "filter": "id:in:[" + ','.join(programRuleVariables_uid) + "]",
                                                      "fields": "id,name,programRuleVariableSourceType,dataElement,trackedEntityAttribute"
                                                      }).json()['programRuleVariables']
        programRules = api_source.get('programRules',
                                      params={"paging": "false",
                                              "filter": "program.id:eq:" + program_uid,
                                              "fields": "id,name,condition"}).json()['programRules']

        programRules_uid = json_extract(programRules, 'id')
        programRules = reindex(programRules, 'id')
        print('Number of Program Rules:' + str(len(programRules_uid)))
        # for uid in programRules:
        #     print('Program Rule: ' + programRules[uid]['name'])

        programRuleActions = api_source.get('programRuleActions',
                                            params={"paging": "false",
                                                    "filter": "programRule.id:in:[" + ','.join(programRules_uid) + "]",
                                                    "fields": "id,name,programRuleActionType,data,content"}).json()[
            'programRuleActions']
        programRuleActions_uid = json_extract(programRuleActions, 'id')
        print('Number of Program Rule Actions:' + str(len(programRuleActions_uid)))

        print('Number of Program Stages:' + str(len(programStages_uid)))
        programStages = api_source.get('programStages',
                                       params={"paging": "false", "order": "sortOrder:asc",
                                               "filter": "id:in:[" + ','.join(programStages_uid) + "]",
                                               "fields": "id,name,executionDateLabel,programStageSections,programStageDataElements"}).json()[
            'programStages']

        for programStage in programStages:
            print('Stage:' + programStage['name'] + " (" + programStage['id'] + ")")
            # Add header to dataframe
            event_date_label = 'Event Date'
            if 'executionDateLabel' in programStage:
                event_date_label = programStage['executionDateLabel']
            df = df.append({"Stage": programStage['name'], "Section": "",
                            "TEA / DE / eventDate": event_date_label,
                            "UID": programStage['id'], "valueType": "DATE", "optionSet": "", "mandatory": 'True'},
                           ignore_index=True)
            des_uid = json_extract_nested_ids(programStage, 'dataElement')

            dataElements = api_source.get('dataElements',
                                          params={"paging": "false",
                                                  "fields": "id,name,categoryCombo,aggregationType,valueType,optionSet",
                                                  "filter": "id:in:[" + ','.join(des_uid) + "]"}).json()[
                'dataElements']
            dataElements = reindex(dataElements, 'id')
            # dataElements = reindex(dataElements, 'id')

            print('Number of DEs:' + str(len(des_uid)))
            if 'programStageSections' in programStage and len(programStage['programStageSections']) > 0:
                programStageSections_uid = json_extract_nested_ids(programStage, 'programStageSections')
                programStageSections = api_source.get('programStageSections',
                                                      params={"paging": "false", "order": "sortOrder:asc",
                                                              "fields": "id,name,dataElements",
                                                              "filter": "id:in:[" + ','.join(
                                                                  programStageSections_uid) + "]"}).json()[
                    'programStageSections']
                dataElements_programStage = dict()
                for elem in programStage['programStageDataElements']:
                    key_value = elem['dataElement']['id']
                    dataElements_programStage[key_value] = elem

                for programStageSection in programStageSections:
                    print("Program Stage Section:" + programStageSection['name'])
                    section_label = programStageSection['name']

                    for dataElement in programStageSection['dataElements']:
                        dataElement_id = dataElement['id']
                        # This will fail if the DE is present in the PSSection but not in the PS, so we check first
                        # if the key exists. If not, we warn the user and skip this
                        if dataElement_id not in dataElements:
                            logger.warning("Data Element with UID " + dataElement_id +
                                           " is present in program stage section but not assigned to the program stage")
                            logger.warning("SKIPPING")
                        else:
                            dataElement_def = dataElements[dataElement_id]
                            dataElement_PS = dataElements_programStage[dataElement_id]
                            print('DE: ' + dataElement_def['name'] + " (" + dataElement_def['valueType'] + ")")
                            optionSet_def = ""

                            if 'optionSet' in dataElement_def:
                                optionSet = dataElement_def['optionSet']['id']
                                if optionSet not in optionSetDict:
                                    options = api_source.get('options', params={"paging": "false",
                                                                                "order": "sortOrder:asc",
                                                                                "fields": "id,code",
                                                                                "filter": "optionSet.id:eq:" + optionSet}).json()[
                                        'options']
                                    optionsList = json_extract(options, 'code')
                                    optionSetDict[optionSet] = optionsList

                                if len(optionsList) <= 20:  # 20 comes from Enzo Rossi :)
                                    optionSet_def = '\n'.join(optionSetDict[optionSet])
                                else:
                                    optionSet_def = '\n'.join(optionSetDict[optionSet][:20]) + '\n(...)'

                            df = df.append({"Stage": "", "Section": section_label,
                                            "TEA / DE / eventDate": dataElement_def['name'],
                                            "UID": dataElement_id, "valueType": dataElement_def['valueType'],
                                            "optionSet": optionSet_def, "mandatory": dataElement_PS['compulsory']},
                                           ignore_index=True)
                        if section_label != "":
                            section_label = ""

            else:  # Assume BASIC todo: create CUSTOM
                for dataElement in programStage['programStageDataElements']:
                    dataElement_id = dataElement['dataElement']['id']
                    dataElement_def = dataElements[dataElement_id]
                    print('DE: ' + dataElement_def['name'] + " (" + dataElement_def['valueType'] + ")")
                    optionSet_def = ""
                    if 'optionSet' in dataElement_def:
                        optionSet = dataElement_def['optionSet']['id']
                        if optionSet not in optionSetDict:
                            options = api_source.get('options', params={"paging": "false",
                                                                        "order": "sortOrder:asc",
                                                                        "fields": "id,code",
                                                                        "filter": "optionSet.id:eq:" + optionSet}).json()[
                                'options']
                            optionsList = json_extract(options, 'code')
                            optionSetDict[optionSet] = optionsList

                        if len(optionsList) <= 20: # 20 comes from Enzo Rossi :)
                            optionSet_def = '\n'.join(optionSetDict[optionSet])
                        else:
                            optionSet_def = '\n'.join(optionSetDict[optionSet][:20]) + '\n(...)'

                        # print('    with optionSet = ' + dataElement['optionSet']['id'])
                    df = df.append({"Stage": "", "Section": "", "TEA / DE / eventDate": dataElement_def['name'],
                                    "UID": dataElement_id, "valueType": dataElement_def['valueType'],
                                    "optionSet": optionSet_def, "mandatory": dataElement['compulsory']},
                                   ignore_index=True)

                # Find out if it is used in programRuleVariable
                # for PRV in programRuleVariables:
                #     if 'dataElement' in PRV and PRV['dataElement']['id'] == dataElement['id']:
                #         print('Used in PRV:' + PRV['name'] + " (" + PRV['id'] + ")")
                # # Find out if used in ProgramRuleAction
                # for PRA in programRuleActions:
                #     if 'dataElement' in PRA and PRA['dataElement']['id'] == dataElement['id']:
                #         print('Used in PRA:' + PRA['name'] + " (" + PRA['id'] + ")")
                #         print('Program Rule:' + programRules[PRA['programRule']['id']]['name'])
        # stages_counter = { 'ang4CLldbIu':25 }
        # df = add_repeatable_stages(df, stages_counter)
        # for tei in list_teis:
        #     if len(tei["enrollments"][0]) > 0:  # and tei["enrollments"][0]["storedBy"] == user:
        #         result = add_json_tei_to_metadata_df(tei, df)
        #
        # export_csv = df.to_csv(r'./program-Case_Based_Surveillance-Dummy_data.csv', index=None, header=True)

        # get TEIs from OU
        if args.OrgUnit is not None:
            params = {
                'ou': args.OrgUnit,
                'ouMode': 'DESCENDANTS',
                'program': program_uid,
                'skipPaging': 'true',
                # 'lastUpdatedDuration': '4d',
                'fields': '*',
                'includeAllAttributes': 'true'
            }

            list_teis = api_source.get('trackedEntityInstances', params=params).json()['trackedEntityInstances']

            logger.info("Found " + str(len(list_teis)) + " TEIs")

            stages_counter = dict()
            for tei in list_teis:
                counter = dict()
                if "enrollments" in tei and len(
                        tei["enrollments"][0]) > 0:  # and tei["enrollments"][0]["storedBy"] == user:
                    if len(tei['enrollments']) == 1:
                        if tei['enrollments'][0]['program'] == program_uid:
                            if 'events' in tei['enrollments'][0]:
                                events = tei['enrollments'][0]['events']
                                for event in events:
                                    if event["programStage"] in counter:
                                        counter[event["programStage"]] += 1
                                    else:
                                        counter[event["programStage"]] = 1
                        else:
                            logger.error(
                                "TEI enrolled in program " + tei['enrollments'][0]['program'] + " not supported")
                    else:
                        logger.error('error, multi-enrollment not supported')
                for key in counter:
                    if key not in stages_counter or stages_counter[key] < counter[key]:
                        stages_counter[key] = counter[key]
                        # logger.info('Found ' + str(stages_counter[key]) + ' instances of ' + key)

            df = add_repeatable_stages(df, stages_counter)
            for tei in list_teis:
                if len(tei["enrollments"][0]) > 0:  # and tei["enrollments"][0]["storedBy"] == user:
                    result = add_json_tei_to_metadata_df(tei, df)

        # Check if there are repeatable stages (only if TEIs were not provided)
        elif args.repeat_stage is not None and len(args.repeat_stage) > 0:
            stages_counter = dict()
            for param in args.repeat_stage:
                stages_counter[param[0]] = int(param[1])
            df = add_repeatable_stages(df, stages_counter)

        # Create the spreadsheet
        url = create_google_spreadsheet(program, df, args.share_with)
        if url != "":
            logger.info('Spreadsheet created here: ' + url)
        else:
            logger.error("Something went wrong")

        # Export to csv
        # export_csv = df.to_csv(r'./program-' + program['name'].replace(' ', '_') + '.csv', index=None, header=True)


if __name__ == '__main__':
    main()
