# DHIS2 USER POPULATOR

A command line tool to populate users for DHIS2 testing from a prescribed set of users.
The users are sent directly to the metadata endpoint for import.

## Requirements

Python3

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install required packages.

```bash
pip install -r requirements.txt
```

Create .env file containing the credentials of the default server to use as well as a file name of the CSV that will have a list of potential new users. 

```
DHIS2_BASE_URL=https://play.dhis2.org/2.34.3/
DHIS2_USERNAME=admin
DHIS2_PASSWORD=district
DHIS2_USERS_FILENAME=test_users.csv
```

NB: CSV header row must contain the following elements:
***firstName, surname, username, password, userRoles, userGroups, organisationUnits, dataViewOrganisationUnits, locale, userGroups***
| firstName | surname | username | password | userRoles | organisationUnits | dataViewOrganisationUnits | locale | userGroups |
| :-------- | :------ | :------: | :------: | :-------: | :---------------- | :------------------------ | :----- | :----------: |

Note that the CSV fields must be delimted by semicolon `;`. For the userRoles, userGroups, organisationUnits and dataViewOrganisationUnits fields, 
you can separate multiple entries with a comma `,`.

## Run

Having prepared a CSV and setup the .env file with respective credentials and csv filename, then run

```bash
python3 userpopulator.py
```