# dhis2-metadata-package-diff

Get differences between package files in json format and creates an excel with the result. Working in Google Spreadsheet is also possible

## Tools for metadata diff

Python 3.6+ is required.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install required packages.

```bash
pip install -r requirements.txt
```
You will need to request the google spreadsheets API token to UiO if you want to work in the cloud


## Usage

Positional arguments:
```
package1.json	json file of previous package (older version) 
package2.json	json file of current package (latest version)
spreadsheet_name the title of the spreadsheet to create or update (if the name matches an existing one)
```

Optional arguments:
```
-ug       use google -> Create or upload a spreadsheet with the results of the diff in Google Spreadsheets. The spreadsheet title comes from spreadsheet_name parameter
-sw       share with -> Add a list of email accounts to share the spreadsheet with
```

Examples:

```bash
python metadata_package_diff.py EIR_TRK_0.9.2_DHIS2.34-en.json EIR_TRK_1.0.2_DHIS2.34.7-EMBARGOED-en.json EIR_TRK-0.9.2-VS-1.02
python metadata_package_diff.py EIR_TRK_0.9.2_DHIS2.34-en.json EIR_TRK_1.0.2_DHIS2.34.7-EMBARGOED-en.json EIR_TRK-0.9.2-VS-1.02 -ug -sw=olav@dhis2.org,yury@dhis2.org
```


## Output

Produces an excel file (optionally a google spreadsheet link) with the comparison of both json giles. This file shows the metadata that has been DELETED, CREATED and UPDATED from one package to another. It also provide a json file package_diff_delete.json which can be imported with strategy DELETE to try to delete the metadata in instances where the old version of the package was installed
