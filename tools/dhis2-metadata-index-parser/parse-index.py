import os
import json
import gspread 
import pandas as pd
from gspread_dataframe import get_as_dataframe


def main() -> None:
    service_account = os.getenv('GC_SERVICE_ACCOUNT')
    spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
    worksheet_name = os.getenv('GOOGLE_WORKSHEET_NAME', 'DHIS2 packages')
    toggle_column = os.getenv('PACKAGE_TOGGLE_COLUMN', 'Extraction Enabled')
    input_columns = json.loads(os.getenv('PACKAGES_INPUT_COLUMNS', '["DHIS2 code for packaging", "Source instance DHIS2.36", "Script parameter"]'))

    spreadsheets = gspread.service_account(filename=service_account)

    worksheet = spreadsheets.open_by_key(spreadsheet_id).worksheet(worksheet_name)
    
    dataframe = get_as_dataframe(worksheet, dtype=str)

    dataframe[toggle_column] = dataframe[toggle_column].map({'True': True, 'TRUE': True, 'False': False, 'FALSE': False})

    result_dataframe = dataframe.loc[dataframe[toggle_column] == True]

    result_dataframe = result_dataframe.fillna("")

    print(json.dumps(result_dataframe[input_columns].to_dict('records')))


if __name__ == '__main__':
    exit(main())
