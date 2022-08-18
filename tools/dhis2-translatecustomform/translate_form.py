# todo: be able to pass the uids of the dataEntryForms as a parameter rather than scanning all instance
import json
import re
from os import path

import Levenshtein as lev
import pandas as pd
from bs4 import BeautifulSoup
from dhis2 import Api, RequestException, setup_logger, logger, generate_uid, \
    is_valid_uid  # make sure you have dhis2.py installed, otherwise run "pip3 install dhis2.py"

try:
    f = open("./auth.json")
except IOError:
    print("Please provide file auth.json with credentials for DHIS2 server")
    exit(1)
else:
    api = Api.from_auth_file('./auth.json')

#          "dhis2.util.on( 'dhis2.de.event.formReady', function( event, ds ) {\n" \
#           "} );\n" \
js_code = "" \
          "console.log('Applying translations');\n" \
          "    $(function() {\n" \
          "        	$.ajax({\n" \
          "        	   type: 'GET',\n" \
          "        	   url: '../api/me.json',\n" \
          "        	   success: function(data){\n" \
          "        	     if('settings' in data) {\n" \
          "                 var locale = data.settings.keyDbLocale;\n" \
          "                 console.log('DB Locale: ' + locale);\n" \
          "        	     }\n" \
          "        	     else {\n" \
          "        	        var locale = document.documentElement.lang;\n" \
          "        	        console.log('Could not get DB locale, using UI locale: ' + locale);\n" \
          "        	     }\n" \
          "              changeLanguage(locale);\n" \
          "            },\n" \
          "            error: function(){\n" \
          "            }\n" \
          "    });\n" \
          "\n" \
          "        function changeLanguage(lang){\n" \
          "            $('.lang').each(function(index,element){\n" \
          "                 $(this).html(arrLang[lang][$(this).attr('langkey')]);\n" \
          "             });\n" \
          "        }\n" \
          "    })\n"
setup_logger()


def find_possible_translations(df, en_string, lang):
    match = ""
    if 'en' in df.columns:
        index = 0
        for english_text in df['en'].tolist():
            if lev.ratio(en_string.lower(), english_text.lower()) > 0.95:
                break
            index += 1
        if index != len(df['en'].tolist()) and lang in df.columns:
            match = df.iloc[index][lang]
    else:
        logger.error('Dataframe does not have en column')

    return match


def generate_key_from_name(name):

    html_escape_table = {
        "!": "#33",
        '"': "#34",
        "$": "#36",
        "%": "#37",
        "&": "#38",
        "'": "#39",
        "(": "#40",
        ")": "#41",
        "*": "#42",
        "+": "#43",
        ",": "#44",
        "-": "#45",
        ".": "#46",
        "/": "#47",
        ":": "#58",
        ";": "#59",
        "<": "#60",
        "=": "#61",
        ">": "#62",
        "?": "#63",
        "≤": "#le",
        "≥": "#ge",
        "|": "#124"

    }
    # Max length = 65
    # For data entry forms we use a key key="dataEntryForm_bla_bla"
    # For Reports we will need to use a key key="htmlReport_bla_bla"

    return 'dataEntryForm_' + "".join(html_escape_table.get(c, c) for c in name.string.lower().strip().replace(" ", "_"))[:65]


if __name__ == '__main__':

    logger.warning("Server source running DHIS2 version {} revision {}".format(api.version, api.revision))

    import argparse

    my_parser = argparse.ArgumentParser(prog='translate_form',
                                        description='Manage translations for custom forms',
                                        epilog="It connects to instance using auth.json file and"
                                               "\n - Creates an excel with key - en translations for the custom forms present"
                                               "\n - Updates the custom form with the translations provided in the excel"
                                               "\nLegend for some warnings/errors:"
                                               "\n - Pair key / EN translations already in dictionary -> The EN string is used multiple times in the custom form but only one entry will be created in the dictionary",
                                        formatter_class=argparse.RawDescriptionHelpFormatter)
    my_parser.add_argument('-get', '--get_dict_from_form', action="store", metavar='file_name',
                           const='dictionary_' + generate_uid(), nargs='?',
                           help="Create dictionary of translatable string from custom forms in the instance."
                                "\nOptionally, you can pass the name of the output file to create."
                                "\nIf an existing xlsx file is provided, it creates a file _new.xlsx with updated keys and EN strings."
                                "\nEg: --get_dict_from_form=my_file_name")
    my_parser.add_argument('-post', '--update_form_from_dict', action="store", metavar='file_name', nargs=1,
                           help="Use dictionary in xlsx format to update translations in form"
                                "\nEg: --update_form_from_dict=my_file.xlsx")
    my_parser.add_argument('-gk', '--generate_keys', action='store_true',
                           help='This optional argument makes sure the keys are regenerated in the html form and the dict')

    args = my_parser.parse_args()

    if args.get_dict_from_form is None and args.update_form_from_dict is None:
        logger.error('Please specify at least one option. Try with -h to check for command line help')
        exit(1)
    mode = 'get'
    if args.get_dict_from_form is not None:
        logger.info("Creating dictionary")
        if '.xlsx' not in args.get_dict_from_form:
            output_file_name = args.get_dict_from_form + '.xlsx'
        print(output_file_name)
    elif args.update_form_from_dict is not None:
        mode = 'post'
        logger.info("Updating custom forms")
        input_file_name = args.update_form_from_dict[0]
        try:
            xls = pd.ExcelFile(input_file_name)
        except FileNotFoundError:
            logger.error('File ' + input_file_name + ' does not exist')

    if mode == 'get':
        # Check if file exists, so we can update it
        update = False
        if path.exists(output_file_name):
            #            xls = pd.ExcelWriter(output_file_name, mode='a')
            xls_read = pd.ExcelFile(output_file_name)
            update = True
            output_file_name = output_file_name.replace(".xlsx", "_new.xlsx")
        xls = pd.ExcelWriter(output_file_name)

        metadataWithCustomForms = list()
        # Check for custom forms in dataSets
        dataSets = api.get('dataSets', params={"paging": "false",
                                               "fields": "id,name,dataEntryForm",
                                               "filter": "formType:eq:CUSTOM"}).json()['dataSets']
        if len(dataSets) > 0:
            metadataWithCustomForms = metadataWithCustomForms + dataSets

        # Check for custom forms in programStages
        programStages = api.get('programStages', params={"paging": "false",
                                                         "fields": "id,name,dataEntryForm",
                                                         "filter": "formType:eq:CUSTOM"}).json()['programStages']
        if len(programStages) > 0:
            metadataWithCustomForms = metadataWithCustomForms + programStages

        logger.info("Found " + str(len(metadataWithCustomForms)) + " custom forms in server")

        # Check for custom reports
        # htmlReports = api.get("") # api/reports/UpFWLROhLW7?fields=designContent
        # if len(htmlReports) > 0:
        #     metadataWithCustomForms = metadataWithCustomForms + htmlReports
        # logger.info("Found " + str(len(htmlReports)) + " custom reports in server")

        for element in metadataWithCustomForms:
            if update:
                element_found = False
                for sheet in xls_read.sheet_names:
                    # Only process the worksheets which have a DHIS2 UID
                    if is_valid_uid(sheet) and sheet == element['id']:
                        # we found the dataSet/programStage in the excel -> get it as df
                        element_found = True
                        df_old = pd.read_excel(xls_read, sheet_name=sheet)
                        df_old.fillna('', inplace=True)

                        if 'key' not in df_old or 'en' not in df_old:
                            logger.error('Worksheet for ' + sheet + ' is missing key and en columns')
                            exit(1)
                        df = pd.DataFrame({}, columns=df_old.columns)
                        break
                if not element_found:
                    df_old = None
                    df = pd.DataFrame({}, columns=['key', 'en'])
            else:
                df = pd.DataFrame({}, columns=['key', 'en'])

            dataEntryFormUID = element['dataEntryForm']['id']
            logger.info(element['name'] + ' - dataEntryForm: ' + dataEntryFormUID)
            form = api.get('dataEntryForms/' + dataEntryFormUID).json()

            if isinstance(form, dict) and 'htmlCode' in form:
                html_code = form['htmlCode']
                if html_code.count('class="lang"') == 0:
                    logger.warning('Skipping element, no lang tags found')
                    continue
                soup = BeautifulSoup(html_code, "html.parser")
                code_modified = False
                for text in soup.findAll("span", {"class": "lang"}):
                    create_or_update_key = False
                    if args.generate_keys:
                        if not text.has_attr('langkey'):
                            old_key = ""
                        else:
                            old_key = text['langkey']
                        create_or_update_key = True

                    else:
                        if not text.has_attr('langkey'):
                            create_or_update_key = True
                        else:
                            key = text['langkey']

                    if create_or_update_key:
                        tag_to_replace = str(text)
                        try:
                            key = generate_key_from_name(text.string)
                        except AttributeError:
                            logger.error(text.text + ' is malformed in html. Please verify form code')
                            content_str = ""
                            for i in range(0,len(text.contents)):
                                content_str += str(text.contents[i])
                            text.string = content_str
                            key = generate_key_from_name(text.string)
                        text['langkey'] = key
                        new_tag = str(text)
                        # Before calling replace, convert entire html code to string
                        html_code = str(soup)
                        html_code = html_code.replace(tag_to_replace, new_tag)
                        code_modified = True

                    text_EN = text.string.strip()
                    # If we are updating an existing dictionary and regenerating keys
                    if args.generate_keys and update and element_found:
                        df_key = df_old[df_old.key == old_key].copy()
                        if df_key.shape[0] != 1:
                            if old_key != "":
                                logger.warning(
                                    'key ' + old_key + ' found in custom form but not in dictionary spreadsheet')
                            new_row_from_dict = {"key": key, "en": text_EN}
                            for lang in df_old.columns:
                                if lang not in new_row_from_dict:
                                    new_row_from_dict[lang] = find_possible_translations(df_old, text.string, lang)
                            df_key = df_key.append(new_row_from_dict, ignore_index=True)
                            # Make sure empty is not NaN
                            df_key.fillna('', inplace=True)
                        else:
                            # Append new row replacing key and en
                            df_key['key'] = key
                            df_key['en'] = text_EN

                        # Do not add duplicate entries
                        if df[df.key == key].shape[0] == 0 and df[df.en == text_EN].shape[0] == 0:
                            df = pd.concat([df, df_key])
                        else:
                            logger.warning('Pair ' + key + ' - ' + text_EN + ' already in dictionary... Skipping')

                    else:
                        new_row_from_dict = {"key": key, "en": text_EN}
                        if update and df_old is not None:
                            for lang in df_old.columns:
                                if lang not in new_row_from_dict:
                                    new_row_from_dict[lang] = find_possible_translations(df_old, text.string, lang)
                        # Do not add duplicate entries
                        if df[df.key == key].shape[0] == 0 and df[df.en == text_EN].shape[0] == 0:
                            df = df.append(new_row_from_dict, ignore_index=True)
                        else:
                            logger.warning('Pair ' + key + ' - ' + text_EN + ' already in dictionary... Skipping')

                if code_modified:
                    logger.info('Updating/creating custom html form keys for translations')
                    try:
                        form['htmlCode'] = html_code
                        # text_file = open("output.html", "w")
                        # text_file.write(html_code)
                        # text_file.close()
                        response = api.put('dataEntryForms/' + dataEntryFormUID,
                                           params={'mergeMode': 'REPLACE'},
                                           json=form)
                    except RequestException as e:
                        # Print errors returned from DHIS2
                        logger.error("dataEntryFormUpdate failed " + str(e))
                        exit(1)

                df.to_excel(xls, element['id'], index=False)
        try:
            xls.save()
        except IndexError:
            pass
    else:
        dataSets = api.get('dataSets', params={"paging": "false",
                                               "fields": "id,name,dataEntryForm",
                                               "filter": "formType:eq:CUSTOM"}).json()['dataSets']
        programStages = api.get('programStages', params={"paging": "false",
                                                         "fields": "id,name,dataEntryForm",
                                                         "filter": "formType:eq:CUSTOM"}).json()['programStages']
        elementsWithCustomForms = dataSets + programStages
        if len(elementsWithCustomForms) == 0:
            logger.error('No custom forms found in instance')
            exit(1)
        for sheet in xls.sheet_names:
            # if sheet != 'OyutuMOPgkt':
            #     continue
            # Only processs the worksheets which have a DHIS2 UID
            if is_valid_uid(sheet):
                for element in elementsWithCustomForms:
                    form = None
                    if element['id'] == sheet:
                        logger.info('Processing element ' + element['id'])
                        dataEntryFormUID = element['dataEntryForm']['id']
                        # Get custom form
                        form = api.get('dataEntryForms/' + dataEntryFormUID).json()
                        if isinstance(form, dict):
                            html_code = form['htmlCode']
                            break

                if form is None:
                    logger.warning(
                        'Element ' + sheet + ' has a translation dictionary in file but does not exist in instance')
                    continue
                soup = BeautifulSoup(html_code, "html.parser")

                df = pd.read_excel(xls, sheet_name=sheet)
                df.fillna('', inplace=True)
                translations_dict = dict()
                if 'key' in df.columns:
                    if df.shape[1] == 1:
                        logger.error('No translations for element ' + sheet)
                    else:
                        # Extract keys
                        keys = df['key'].tolist()
                        for col in df.columns:
                            if col != 'key' and re.match(r"[a-z]{2}(_[A-Z]{2})*", col):
                                # Extract translations
                                values = df[col].tolist()
                                translations_dict[col] = dict(zip(keys, values))

                        js_translations = '\nvar arrLang = ' \
                                          + json.dumps(translations_dict, indent=4, sort_keys=True, ensure_ascii=False)

                        for tag in soup.findAll('script'):
                            # Use extract to remove the tag
                            tag.extract()
                        # Insert both the function and the dictionary at the end of html code
                        new_script = soup.new_tag('script')
                        new_script.string = js_translations + '\n' + js_code
                        soup.insert(len(soup.contents), new_script)

                        try:
                            form['htmlCode'] = str(soup)
                            response = api.put('dataEntryForms/' + dataEntryFormUID,
                                               params={'mergeMode': 'REPLACE'},
                                               json=form)
                        except RequestException as e:
                            # Print errors returned from DHIS2
                            logger.error("dataEntryFormUpdate failed " + str(e))
                            exit(1)

                        # print(soup.prettify())

                else:
                    logger.error('key column missing for element ' + sheet)
