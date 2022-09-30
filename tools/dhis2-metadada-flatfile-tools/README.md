# dhis2-metadata-flatfile-tools

Set of tools to work with flat files

## Tools for metadata diff

Python 3.6+ is required.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install required packages.

```bash
pip install -r requirements.txt
```

Create auth.json file containing the credentials of the default server to use. The script relies on a username 'robot' with SuperUser role to have an account in the server.

```json
{
  "dhis": {
    "baseurl": "https://who-dev.dhis2.org/tracker_dev",
    "username": "robot",
    "password": "TOPSECRET"
  }
}
```

To be able to work in Google Spreadsheets, the script needs a token in the form of credentials.json. Please contact manuel@dhis2.org to get a token


## Usage

generic_metadata_importer

Used to update an instance metadata from a flat file
The flat file must be shared with user python-gspread@dummy-data-297922.iam.gserviceaccount.com and must contain "Flat File" in the name. Credentials to connect are in auth.json

Just run it with python, no arguments needed

```bash
python generic_metadata_importer.py
```

generic_metadata_converter

Used to create a flat file in excel from an instance. Credentials to connect are in auth.json

Positional arguments:
```
Google Spreadsheet Name		It will be used to locate the spreadsheet in the cloud and either update or create it. For the moment in the beta version, any formulas, conditional formating or data validation in the spreadsheet are lost during the update
Instance URL				The instance from which the metadata will be extracted
Configuration				A .conf file which has the format metadataType:column1,column2,...,columnN (please see example provided)

```
Examples:

```bash
python generic_metadata_converter.py "AFI Metadata Flat File" https://who.sandbox.dhis2.org/test_import_237 metadata_types.conf
```


## Output

