import sys
import gspread

# Load the credentials from the JSON file
google_spreadshseet_credentials = 'd2pack-token-e9bbfebebff6c66afd061ceb4b7e3b1a2bc68471.json'
gc = gspread.service_account(filename=google_spreadshseet_credentials)

# Specify the ID of the spreadsheet to delete
spreadsheet_id = sys.argv[1]

# Delete the spreadsheet
gc.del_spreadsheet(spreadsheet_id)

print("Spreadsheet with ID {spreadsheet_id} has been deleted.")