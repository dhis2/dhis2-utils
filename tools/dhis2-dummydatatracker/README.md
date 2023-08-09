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
```
	positional mandatory arguments:
  		program_uid           the uid of the program to use
  	optional arguments:
	  -h, --help            show the help message and exit
	  -wtf ORGUNIT, --with_teis_from ORGUNIT
	                        Pulls TEIs from specified org unit and adds them to flat file (TRK program). Eg: --with_teis_from_ou=Q7RbNZcHrQ9
	  -wte ORGUNIT, --with_events_from ORGUNIT
	                        Pulls Events from specified org unit and adds them to flat file (EVT program). Eg: --with_teis_from_ou=Q7RbNZcHrQ9
	  -rs stage_uid number_repeats, --repeat_stage stage_uid number_repeats
	                        provide a stage uid which is REPEATABLE and specify how many times you are planning to enter it. Eg: --repeat_stage QXtjg5dh34A 3
	  -sw email, --share_with email
	                        email address to share the generated spreadsheet with as OWNER. Eg: --share_with=peter@dhis2.org
   
```
   Important: create_flat_file.py uses the instance URL and credentials in auth.json to access the instance

Examples:
```bash
python create_flat_file.py Lt6P15ps7f6 --with_teis_from=GZ5Ty90HtW --share_with=johndoe@dhis2.org

python create_flat_file Lt6P15ps7f6 --repeat_stage Hj38Uhfo012 5 --repeat_stage 77Ujkfoi9kG 3 --share_with=person1@dhis2.org --share_with=person2@dhis2.org
```

2. Create the dummy TEIs from flat file.
```
	positional mandatory arguments:
	  document_id  the id of the spreadsheet to use

	optional arguments:
	  -h, --help   show the help message and exit

	For https://docs.google.com/spreadsheets/d/1xOeOpz4lSTdtiAJTuLwx40GgC5n9fkH2gltiB-sHmwg do:
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

## Workflow

- Make sure your local files are up to date and contain the latest version in master. See [git pull](https://bit.ly/3uGypaO)
- First time dummy data is going to be injected
	- Call create_flat_file to generate the spreadsheet. Please communicate the ID of the spreadsheet to the team and save it here: https://docs.google.com/spreadsheets/d/1YcP829U70qIqPcU8mQACkPLP2PzwPB-s6RnbVQaMubQ/edit#gid=0
	-  Create the primal TEIs or Events: 
		-  Using DHIS2 UI by creating them in ONE OU and using parameter -wtf / -wte when you can create_flat_file
		-  Using the spreadsheet. Make sure the mandatory fields are filled and pay special attention to the value type of the data you enter.
	- Create a DISTRIBUTION Sheet if needed. It allows customizing the way the values for Data Elements and Tracked Entity Attributes are created. It also allows controlling the enrollment date of the TEIs created as well as the OU where they are enrolled and subsequent events are registered. The sheet must contains the columns: UID, NAME (optional), VALUE, TEI_1, TEI_2.... Columns TEI_X contain the ratio to apply for each possible value (options) or value range (number)
			An example:


		| UID         | NAME                                      | VALUE                 | TEI\_0 | TEI\_1 |
		| :---------- | :---------------------------------------: | :-------------------: | :----: | -----: |
		| Xh88p1nyefp | Enrollment date                           | 2018-12-01:2018-12-28 |        | 0.05   |
		|             |                                           | 2019-01-01:2019-01-28 |        | 0.05   |
		|             |                                           | 2019-02-01:2019-02-28 | 0.1    | 0.05   |
		|             |                                           | 2019-03-01:2019-03-28 | 0.1    | 0.05   |
		|             |                                           | 2019-04-01:2019-04-28 | 0.1    | 0.05   |
		| Jt68iauILtD | HIV Case Surveillance Gender M, F, TG     | Male                  | 0      | 1      |
		|             |                                           | Female                | 0      | 0      |
		|             |                                           | TG                    | 1      | 0      |
		|             |                                           | OTHER                 | 0      | 0      |
		| mAWcalQYYyk | HIV Case Surveillance Date of birth (age) | 0:4                   |        | 0      |
		|             |                                           | 5:9                   | 0      | 0      |
		|             |                                           | 10:14                 | 0      | 0.1    |
		|             |                                           | 15:19                 | 0.2    | 0.1    |
		|             |                                           | 20:24                 | 0.3    | 0.3    |
		|             |                                           | 25:50                 | 0.4    | 0.4    |
		|             |                                           | 51:80                 | 0.1    | 0.1    |
		|             |                                           |                       |        |        |
		| cDt3CvgtlQs | HIV Probable Mode of Transmission         | HETEROSEXUAL          | 0      | 0.4    |
		|             |                                           | INJECTINGDRUG         | 0.2    | 0.1    |
		|             |                                           | MOTHERTOCHILD         | 0.1    | 0      |
		|             |                                           | OTHERUNDETERMINED     | 0.2    | 0.1    |
		|             |                                           | HOMOSEX               | 0.1    | 0.35   |
		|             |                                           | Commercial\_Sex       | 0.4    | 0.05   |

		We can read this as follows: For TEI_0, 20% of the total TEIs to generate must have an age between 15 and 19, 30% an age between 20 and 24 and so forth.
                If you want to distribute by organisation units you need to use the key words you can see in the example below. You can then distribute by Org Unit Group, by specific OUs given by UID or names, etc...
   		| UID         | NAME                  | VALUE              | TEI\_0 | TEI\_1 | TEI\_2 |
   		| :---------- | :-------------------: | :----------------: | :----: | -----: | -----: |
   		| orgUnitUIDs | Organisation Unit     |	OUG{aT5pkgRLbw5}   | 1      | 0      | 0      |
   		|             |                       |	OUG{RbJ4hRSGQaH}   | 0      | 1      | 0      |
   		|             |                       |	OUG{dV8Ec2zJrze}   | 0      | 0      | 1      |
	- Create a RULES tab: this can be sued to write simple expressions to force certain values when randomization could create abnormal situations. For example, to force Sex to be FEMALE if status is PREGNANT. These are some examples from HFA package:
   		| EXPRESSION	                                                |                                     |
   		| :-----------------------------------------------------------: | :---------------------------------: |
   		| if #{aa9ulv0QpC3} == 'false': #{WfmACfSH6Pl} = 'false'        | If no HIV service, no HIV details   |
   		| if #{aa9ulv0QpC3} == 'false': #{ee1ZTOL80hx} = 'false'        | If no HIV service, no HIV details   |
   		| if #{aa9ulv0QpC3} == 'false': #{tKatq8QO7WA} = 'false'        | If no HIV service, no HIV details   |
            Or from HIV package:
   		| EXPRESSION	                                                |                                     |
   		| :-----------------------------------------------------------: | :---------------------------------: |
   		| if #{CklPZdOd6H1} == 'MALE' : #{BfNZcj99yz4} = 'NOT_PREGNANT' | If Male, always not pregnant        |
	- When the spreadsheet is ready please review the following parameters:
		- NUMBER_REPLICAS: make sure the identifiers match the columns in DUMMY_DATA, i.e. if you have a primal TEI called TEI_1, TEI_1 must be present in the rows of NUMBER_REPLICAS if you want to create replicas of this TEI.
		- PARAMETERS: verify server_url, orgUnit_level and metadata_version. Make sure server_url is empty if you want to simple use the server specified in auth.json or that the server url is correct. Make sure orgUnit_level corresponds to the facility level in your OU tree. **Remember that the spreadsheet is a collaborative tool and many users have access to it**, so somebody might have changed the parameters without warning the implementer.

- Spreadsheet already exists and you want to inject new dummy data.	
	- First and most important: **RUN create_flat_file to update the metadata in the spreadsheet**
	- Adjust the primal TEIs if necessary so they match the latest metadata for the package. For example, if a new DE has been added and it is mandatory, you need to make sure this DE has a value for all the primal TEIs.
	- If adjusting the primal TEIs is too cumbersome, feel free to create them again using the UI and importing them by using -wtf parameter in create_flat_file.

When the metadata is up to date, the primal TEIs are created and NUMBER_REPLICAS, PARAMETERS and DISTRIBUTION sheets have been correctly configured, you are ready to call create_TEIs with the id of the spreadsheet. The data entered for the primal TEIs will be validated and, if errors are found, they will be highlighted in red in DUMMY_DATA sheet. A new sheet containing the results of the validation will also be added to the spreadsheet for your convinience. If no errors are found or parameter ignore_errors = True, the script will start injecting TEIs in the target server specified by server_url in chunks of max_chunk_size.
