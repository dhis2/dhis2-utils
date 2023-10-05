import argparse
import json
import gspread
from gspread_dataframe import get_as_dataframe


def get_input_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--service-account-file', required=True, type=str, help='Google Service Account file. (more details at https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account)')
    parser.add_argument('--spreadsheet-id', required=True, type=str, help='Google Spreadsheet ID.')
    parser.add_argument('--worksheet-name', type=str, default='DHIS2 packages', help='Google Spreadsheet Worksheet name.')
    parser.add_argument('--toggle-column', type=str, default='Enabled', help='Packages toggle column.')
    parser.add_argument('--readiness-column', type=str, default='Ready For Export', help='Packages readiness column.')
    parser.add_argument('--input-columns', type=str, default='["Package Code", "Package Type",  "Source Instance", "Component Name", "Supported DHIS2 Versions", "Health Area", "Health Area Code"]', help='Packages input columns.')
    parser.add_argument('--uncheck-readiness', action='store_true', help='Uncheck packages readiness column.')
    parser.add_argument('--no-uncheck-readiness', dest='uncheck_readiness', action='store_false', help='Don\'t uncheck packages readiness column.')
    parser.set_defaults(uncheck_readiness=True)
    parser.add_argument('--only-ready', action='store_true', help='Get input columns data only for ready packages.')
    parser.add_argument('--no-only-ready', dest='only_ready', action='store_false', help='Get input columns data for all packages.')
    parser.set_defaults(only_ready=True)

    return parser.parse_args()


def update_readiness_checkbox(worksheet, column_name) -> None:
    checked_packages = worksheet.findall("TRUE", in_column=column_name)

    for checkbox in checked_packages:
        checkbox.value = False

    if checked_packages:
        worksheet.update_cells(checked_packages)


def main() -> None:
    args = get_input_args()

    spreadsheets = gspread.service_account(filename=args.service_account_file)

    worksheet = spreadsheets.open_by_key(args.spreadsheet_id).worksheet(args.worksheet_name)
    
    # get worksheet values as strings to avoid evaluating "boolean" values as floats
    dataframe = get_as_dataframe(worksheet, dtype=str)

    # replace "string boolean" values with actual booleans
    dataframe[[args.toggle_column, args.readiness_column]] = dataframe[[args.toggle_column, args.readiness_column]].replace({'True': True, 'TRUE': True, 'False': False, 'FALSE': False})

    # filter only enabled packages
    dataframe = dataframe.loc[(dataframe[args.toggle_column] == True)]

    if args.only_ready:
        dataframe = dataframe.loc[(dataframe[args.readiness_column] == True)]

    dataframe = dataframe.fillna("")

    # get the 1-based index of the readiness column
    readiness_column_index = worksheet.row_values(1).index(args.readiness_column) + 1

    if args.uncheck_readiness:
        update_readiness_checkbox(worksheet, readiness_column_index)

    print(json.dumps(dataframe[json.loads(args.input_columns)].to_dict('records')))


if __name__ == '__main__':
    exit(main())
