# dhis2-dummydataagg

Tool box to generate and manage dummy data in Tracker

## Tools for dummy data generation in Aggregated

Python 3.6+ is required.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install required packages.

```bash
pip install -r requirements.txt
```

Create/modify auth.json file containing the credentials of the default server to use. Use a Superuser account and provide the full URL without the /api part. See example below:

```json
{
  "dhis": {
    "baseurl": "https://who-dev.dhis2.org/dev",
    "username": "admin",
    "password": "district"
  }
}
```

## Usage

	positional mandatory arguments:
  	   dataset_param        UIDs of dataSets to generate for separated by commas, or a prefix to filter the dataSets by name, e.g. HIV
  	optional arguments:
	  -h, --help            show the help message and exit
	  -sd START_DATE        data generated will start from start date
	  -ed END_DATE          data will be generated until end date, being today the default date to use if not specified
	  -ptf PERIOD_TYPE_FILTER can be d, w, m, q, y    this options allows processing only dataSets for a specific time frequency from all the dataSets which will match the prefix search
	  -ous TYPE VALUE      this parameters is used to specify the OUs which data will be generated for. From all the options available:
	      type=uid           value is a comma separated list of OU uids to use
	      type=uid_children  uses the children OUs of OU specified by a list of parent UIDs separated by commas
	      type=name          uses the OU given by a list of names separated by commas
	      type=ilike         uses a keyword to search for OUs by name (not case sensitive)
	      type=code          a list of OU codes to use separated by commas
	      type=level         all OUs in a specific OU level
	  -cf [FILE_NAME]        create a flat file with DEs and COCs to allow specifying value ranges.The file name can be specified as parameter. This operation won't create any dummy data
	  -uf FILE_NAME          uses a previously created (using cf) spreadsheet with value ranges to generate the dummy data
	  
Examples:
```bash
python create_data.py Lt6P15ps7f6 -sd=2021-01-01 -ed=2021-04-30 -ous level 4

python create_data.py HIV -sd=2021-01-01 -ous name "Health facility" -uf test.csv

python create_data.py HIV -cf hiv_dataset_value_ranges.csv
```
