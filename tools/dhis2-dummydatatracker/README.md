# dhis2-dummydatatracker

Tool box to generate and manage dummy data in Tracker

## Tools for dummy data generation in Tracker

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

1. Create a flat file in Google Spreadsheets for your program. If a flat file already matches, the GSpreadsheet is updated.
	positional mandatory arguments:
  		program_uid           the uid of the program to use
  	optional arguments:
	  -h, --help            show the help message and exit
	  -wtf ORGUNIT, --with_teis_from ORGUNIT
	                        Pulls TEIs from specified org unit and adds them to flat file. Eg: --with_teis_from_ou=Q7RbNZcHrQ9
	  -rs stage_uid number_repeats, --repeat_stage stage_uid number_repeats
	                        provide a stage uid which is REPEATABLE and specify how many times you are planning to enter it. Eg: --repeat_stage QXtjg5dh34A 3
	  -sw email, --share_with email
	                        email address to share the generated spreadsheet with as OWNER. Eg: --share_with=peter@dhis2.org

```bash
python create_flat_file.py Lt6P15ps7f6 --with_teis_from_ou=GZ5Ty90HtW --share_with=johndoe@dhis2.org

python create_flat_file Lt6P15ps7f6 --repeat_stage Hj38Uhfo012 5 --repeat_stage 77Ujkfoi9kG 3 --share_with=person1@dhis2.org --share_with=person2@dhis2.org
```

2. Create the dummy TEIs from flat file.
	positional mandatory arguments:
	  document_id  the id of the spreadsheet to use

	optional arguments:
	  -h, --help   show the help message and exit

	For https://docs.google.com/spreadsheets/d/1xOeOpz4lSTdtiAJTuLwx40GgC5n9fkH2gltiB-sHmwg do:

```bash
python create_TEIs.py 1xOeOpz4lSTdtiAJTuLwx40GgC5n9fkH2gltiB-sHmwg
```

3. Remove dummy data if needed. Script takes no arguments (currently is a draft)

```bash
python delete_TEIs.py
```	

4. Remove google spreadsheet created with create_flat_file:

```bash
python delete_sh.py 1xOeOpz4lSTdtiAJTuLwx40GgC5n9fkH2gltiB-sHmwg
```	


