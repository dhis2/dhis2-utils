# dhis2-utils

Resources, tools and utils for DHIS 2

## Tools for test data generation

| Tool | Summary |
| :--- | :------ |
| [DHIS2 DATAGEN](tools/dhis2-datagen) | A command line tool to generate large amount of data for performance test of the DHIS2 application. _This application generates a file containing INSERT statements that can be imported into the database._ |
| [DHIS2 Org Unit Generator](tools/dhis2-org-generator) | A command line tool to generate Org Unit hierarchies. _This application POSTs OUs directly to an instance._ |
| [DHIS2 Dummy Data generator for Tracker](tools/dhis2-dummydatatracker) | A command line tool to generate dummy data for tracker packages. _This application creates a flat file where primal TEIs can be created and then uses that to post replicas of those TEIs to the server._ |
| [DHIS2 Dummy Data generator for Aggregate](tools/dhis2-dummydataagg) | A command line tool to generate random dummy data for agg packages. _This application creates a flat file where value intervals can be defined to fine tune the data creation._ |
| [DHIS2 User Populator](tools/dhis2-user-populator) | A command line tool to populate dummy users. _This application creates users in bulk, given user details in a CSV file._ |
| [DHIS2 Data Time Shifter](tools/dhis2-data-time-shifter) | Two SQL functions to shift in time Tracker/Event and Aggregate data. Useful for demo instances or training DBs |
| [DHIS2 Time Shift Tools](tools/dhis2-time-shift-tools) | A suite of tools for keeping test and demo databases up to date. |

## Tools for metadata packages

| Tool | Summary |
| :--- | :------ |
| [Metadata Package Validator](tools/dhis2-metadata-package-validator) | A command line tool to validate a metadata package.|
| [Metadata Translator](/tools/dhis2-metadata-translator) | A command line tool to push package strings to and from Transifex. |
