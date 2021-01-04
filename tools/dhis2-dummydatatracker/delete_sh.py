import gspread
from oauth2client.service_account import ServiceAccountCredentials
import sys

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('dummy-data-297922-97b90db83bdc.json', scope)

docid = sys.argv[1]

client = gspread.authorize(credentials)

gc = gspread.authorize(credentials)
gc.del_spreadsheet(docid)
