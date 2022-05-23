# dhis2-metadata-index-parser

Python script for reading the DHIS2 Metadata Packages index and parsing input parameters for CI/CD pipelines.

## Installation

`pip install -r requirements.txt`

## Usage

`python parse-index.py`

### Required Env variables
* `GC_SERVICE_ACCOUNT` - path to Service Account credentials file ([more details here](https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account))
* `GOOGLE_SPREADSHEET_ID` - Google Spreadsheet ID

### Optional Env variables (these have default values embedded in the script)
* `GOOGLE_WORKSHEET_NAME` - Google Spreadsheet Worksheet name
* `PACKAGE_TOGGLE_COLUMN` - Name of the column containing toggle for extraction of a given package
* `PACKAGES_INPUT_COLUMNS` - List of column names to include as input for CI/CD params (as JSON string) 
