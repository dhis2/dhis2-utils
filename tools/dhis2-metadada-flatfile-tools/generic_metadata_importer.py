import json
import pandas as pd
import numpy as np
from dhis2 import RequestException, Api, setup_logger, logger
from urllib.request import urlopen

from tkinter import *
from tkinter import filedialog as fd
from tkinter import scrolledtext as st
from tkinter.messagebox import showinfo

from oauth2client.service_account import ServiceAccountCredentials
import gspread
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from gspread_formatting import *
from gspread.exceptions import APIError

from os.path import exists
import validators
#setup_logger()


def log_msg(msg, type='info'):
    Output.insert(END, msg + "\n", type)
    root.update()


def post_to_server(api, jsonObject, apiObject='metadata', strategy='CREATE_AND_UPDATE', mergeMode='REPLACE'):
    try:
        response = api.post(apiObject, params={'mergeMode': mergeMode, 'importStrategy': strategy},
                                   json=jsonObject)

    except RequestException as e:
        # Print errors returned from DHIS2
        log_msg("metadata update failed with error " + str(e), 'error')
        pass
    else:
        if response is None:
            log_msg("Error in response from server", 'error')
            return
        text = json.loads(response.text)
        # print(text)
        if text['status'] == 'ERROR':
            log_msg("Import failed!!!!\n" + json.dumps(text['typeReports'], indent=4, sort_keys=True), 'error')
            with open('post_error.json', 'w') as f:
                json.dump(text['typeReports'], f, indent=4, sort_keys=True)
            return False
        # errorCode = errorReport['errorCode']
        else:
            if apiObject == 'metadata':
                log_msg("metadata imported " + text['status'] + " " + json.dumps(text['stats']))
            else:
                # logger.info("data imported " + text['status'] + " " + json.dumps(text['importCount']))
                log_msg("Data imported\n" + json.dumps(text, indent=4, sort_keys=True))
                with open('post_error.json', 'w') as f:
                    json.dump(text, f, indent=4, sort_keys=True)
                if text['status'] == 'WARNING': log_msg(text, 'warning')
            return True


def select_file():
    filetypes = (
        ('text files', '*.xlsx'),
        ('All files', '*.*')
    )

    excel_file = fd.askopenfilename(
        title='Open a file',
        initialdir='/',
        filetypes=filetypes)

    try:
        xls = pd.ExcelFile(excel_file)
    except FileNotFoundError:
        log_msg('File ' + excel_file + ' does not exist', 'error')
        return

    select_file.xls = xls
    label1['text'] = excel_file



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


def main():

    # my_parser = argparse.ArgumentParser(description='Generic metadata importer')
    # my_parser.add_argument('metadata_type', metavar='metadata_type', type=str,
    #                        help='')
    # my_parser.add_argument('csv_file', metavar='csv_file', type=str,
    #                        help='')
    # my_parser.add_argument('instance', metavar='instance', type=str,
    #                        help='')
    # my_parser.add_argument('-u', '--user', action="store", dest="user", type=str)
    # my_parser.add_argument('-p', '--password', action="store", dest="password", type=str)
    # args = my_parser.parse_args()

    #excel_file = inputfile.get("1.0", "end-1c")
    # if excel_file == "":
    #     log_msg('Please provide an excel file to open', 'error')
    #     return
    # elif '.xlsx' not in excel_file:
    #     excel_file = excel_file + '.xlsx'
    # try:
    #     xls = pd.ExcelFile(excel_file)
    # except FileNotFoundError:
    #     #logger.error('File ' + excel_file + ' does not exist')
    #     log_msg('File ' + excel_file + ' does not exist', 'error')
    #     return

    xls_name = variable_xls.get() #select_file.xls
    sh = gc.open(xls_name)

    instance_url = variable.get()

    metadata_type_selection = variable_meta_type.get()
    global metadata_types_supported
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
    credentials_file = 'auth.json'
    try:
        f = open(credentials_file)
    except IOError:
        print("Please provide file auth.json with credentials for DHIS2 server")
        exit(1)
    else:
        with open(credentials_file, 'r') as json_file:
            credentials = json.load(json_file)
        log_msg('Connected to API in ' + instance_url + ' as user: ' + credentials['dhis']['username'])
        api_source = Api(instance_url, credentials['dhis']['username'], credentials['dhis']['password'])

    sheets_to_process = list()
    for ws in sh.worksheets():
        if ws.title in metadata_type_user_selection:
            sheets_to_process.append(ws.title)
        else:
            supported = False
            for metadata_type in metadata_types_supported:
                if ws.title == metadata_type:
                    supported = True
                    break
                elif '+' in metadata_type:
                    expanded_metadata_type = metadata_type.split('+')
                    if ws.title in expanded_metadata_type:
                        supported = True
                        break
            if not supported:
                log_msg('** Skipping ' + ws.title + ": metadata type is not supported", 'warning')

        multilevel_identifiers = ['programStageDataElements', 'programTrackedEntityAttributes', 'dataSetElements', 'attributeValues']

    for metadata_type in metadata_type_user_selection:

        if metadata_type in sheets_to_process:
            log_msg('** Processing ' + metadata_type)
            # Retain the original name for the metadata type, before removing spaces, etc...
            # Assuming there is only one multilevel
            identifier_name = ""
            df_multilevel_dict = {}
            metadata_type_selection = metadata_type

            # Load sheet/csv as dataframe and convert to json
            df = get_as_dataframe(sh.worksheet(metadata_type), evaluate_formulas=True, na_filter=False)
            #df = pd.read_excel(xls, sheet_name=metadata_type, na_filter=False)
            if df.shape[0] == 0 or (df['id'] == '').sum() == df.shape[0]:
                continue
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
            df = df.drop(df.index[df[df['id'] == ''].index.tolist()])
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
                                    # Consider for now that they are all part of the same dictionary
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

            json_payload = get_json_payload_to_instance(api_source, metadata_type, json_payload, index_elements_to_delete)
            if metadata_type == "optionSets":
                json_payload = {**json_payload,  **get_json_payload_to_instance(api_source, 'options', json_options_payload, index_options_to_delete)}
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


            print(json.dumps(json_payload, indent=4))
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
                            result = post_to_server(api_source, all_json_payload, mergeMode='REPLACE')
                            result = post_to_server(api_source, all_json_payload, mergeMode='MERGE')
            else:
                result = post_to_server(api_source, json_payload)

# The order is important!!
metadata_types_supported = ["Attributes", "Legend Sets", "Option Sets", "Category Options", "Categories", "Category Combos", "Data Elements", "Data Element Groups", "Tracked Entity Attributes", "Tracked Entity Types", "Indicator Types", "Indicators", "Indicator Groups",
                            "Datasets", "Sections", "Programs+Program Stages", "Program Sections", "Program Stage Sections", "Validation Rules", "Program Rule Variables", "Program Rules+Program Rule Actions"]


root = Tk()
root.geometry("800x600")
root.title("Metadata Flat File Import")

# open button
# open_button = Button(
#     root,
#     text='Open Flat File',
#     command=select_file
# )
label1 = Label(text='Please choose a flat file')

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
except Exception as e:
    logger.error('Wrong Google Credentials')
    sys.exit()

flat_files=list()
for sh in gc.openall():
    if 'Flat File' in sh.title:
        flat_files.append(sh.title)
flat_files.sort()

variable_xls = StringVar(root)
variable_xls.set("") # default value
select_xls = OptionMenu(root, variable_xls, *flat_files)

# Get instances in sandbox
label2 = Label(text='Please choose a that target instance to import')
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

variable = StringVar(root)
variable.set(instances[0]) # default value

select_instance = OptionMenu(root, variable, *instances)

variable_meta_type = StringVar(root)
variable_meta_type.set('All')

two_elements_frame = Frame(root)
label3 = Label(two_elements_frame, text='Metadata type to import')
select_metadata_type = OptionMenu(two_elements_frame, variable_meta_type, *(['All'] + metadata_types_supported))

import_button = Button(root, height=2,
                 width=20,
                 text="IMPORT",
                 command=lambda: main())

Output = st.ScrolledText(root, height =30,
              width = 90,
              bg = "white")

Output.tag_config('info', foreground="green")
Output.tag_config('warning', foreground="orange")
Output.tag_config('error', foreground="red")

# l.pack()
# inputfile.pack()
#open_button.pack(expand=True, pady=5)
label1.pack(padx=2, pady=2)
select_xls.pack(pady=5)
label2.pack(padx=2, pady=2)
select_instance.pack(pady=5)
# label2.pack(padx=2, pady=2)
# select_metadata_type.pack(padx=5, pady=2)
two_elements_frame.pack()
label3.grid(row=0, column=0)
select_metadata_type.grid(row=0, column=1)
import_button.pack(pady=5)
Output.pack(fill='both', expand=True)

mainloop()


# if __name__ == "__main__":
#     main()
