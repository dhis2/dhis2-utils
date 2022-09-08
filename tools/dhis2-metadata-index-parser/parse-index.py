import os
import json
import gspread
from gspread_dataframe import get_as_dataframe


def main() -> None:
    service_account = os.getenv('GC_SERVICE_ACCOUNT_FILE')
    spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
    worksheet_name = os.getenv('GOOGLE_WORKSHEET_NAME', 'DHIS2 packages')
    toggle_column = os.getenv('PACKAGE_TOGGLE_COLUMN', 'Extraction Enabled')
    readiness_column = os.getenv('PACKAGE_READINESS_COLUMN', 'Ready for Export')
    input_columns = json.loads(os.getenv('PACKAGES_EXPORT_INPUT_COLUMNS', '["DHIS2 code for packaging", "Source instance", "Script parameter", "Component name"]'))

    spreadsheets = gspread.service_account(filename=service_account)

    worksheet = spreadsheets.open_by_key(spreadsheet_id).worksheet(worksheet_name)
    
    # get worksheet values as strings to avoid evaluating "boolean" values as floats
    dataframe = get_as_dataframe(worksheet, dtype=str)

    # replace "string boolean" values with actual booleans
    dataframe[[toggle_column, readiness_column]] = dataframe[[toggle_column, readiness_column]].replace({'True': True, 'TRUE': True, 'False': False, 'FALSE': False})

    result_dataframe = dataframe.loc[(dataframe[toggle_column] == True) & (dataframe[readiness_column] == True)]

    result_dataframe = result_dataframe.fillna("")

    # get the 1-based index of the readiness column
    readiness_column_index = worksheet.row_values(1).index(readiness_column) + 1

    checked_packages = worksheet.findall("TRUE", in_column=readiness_column_index)

    for checkbox in checked_packages:
        checkbox.value = False

    if checked_packages:
        worksheet.update_cells(checked_packages)

    print(json.dumps(result_dataframe[input_columns].to_dict('records')))


if __name__ == '__main__':
    exit(main())
