# dhis2-package-exporter

Tool box to generate standalone metadata packages

## Tools for metadata package generation

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


## Usage

Positional arguments:
```
program_uid / dataset_uid / AGG		The UID of the progra or dataset to use. If AGG is specified, rather than matching on UID, the script packages all dataSets whose code starts with the package prefix 
Health_area   				The health_area of the package, e.g. HIV, TB, EPI, COVID19
Intervention      			The intervention e.g. CS, EIR, etc..
+ 
optional arguments:
  -h, --help            show the help
  -pf PACKAGE_PREFIX  --package_prefix to use. If not specified, the default package prefix is "Health area"_"Intervention". The elements to package are matched in the code.
  -v PACKAGE_VERSION, --version PACKAGE_VERSION
                        the package version to use
  -i INSTANCE,        --instance INSTANCE
                        instance to extract the package from (robot account is required!) - tracker_dev byu default
  -desc DESCRIPTION,  --description DESCRIPTION
                        Description of the package or any comments you want to add
```
Examples:


```bash
python package_exporter.py M3xtLkYBlKI MAL FOCI -v=1.0.1 -i=https://who.sandbox.dhis2.org/tracker_dev234 -desc="Fix for dashboards"

python package_exporter.py SSLpOM0r1U7 EPI EIR -v=1.0.2 -desc="Patch" -i=https://metadata.dev.dhis2.org/tracker_dev -pf=EIR

python package_exporter.py AGG CH ADO -v=1.0.0 -desc="First package release" -i=https://metadata.dev.dhis2.org/dev
```


## Packaging rules

The following metadata is packaged based on the use of a prefix in the code:
- userGroups
- dashboards
- dataElementGroups
- indicatorGroups
- predictorGroups
- validationRuleGroups

The following metadata is packaged when being assigned to the corresponding group:
- dataElements FROM dataElementGroups
- indicators FROM indicatorGroups
- predictorGroups FROM predictorGroups
- validationRules FROM validationRuleGroups

The script will check references which may have been omitted by the implementer but which need to be included. In some cases it will warn the user that it is automatically adding a reference or it will give an error, exiting with code 1.

An example of this logic:  
- [ ] Get the dataElementGroup with code using the package prefix
- [ ] From the dataElementGroup, get all dataElements to include in the package
- [ ] Check for DEs used in Program Rules (via PRV or PRA)... Anything missing?  
- [ ] Check for DEs used in Indicators and Program Indicators... Anything missing?
- [ ] Check for DEs used in a dashboard item... Anything missing?

Etc...
  
**Log examples**
```
WARNING  2021-10-25 17:58:23,378  Program stage use dataElements not assigned to any programStageSection: ['xMkkGCwSaDK', 'cNA9EmFaiAa', 'J0dqTnGzX6T', 'HGjbAPoyEBu', 'Y3eDHMTcSYk', 'OWolh3WKA3Q', 'knh2BOb3F0I', 'NxVIX3mIhGt']
```
DataElements may not be assigned to a section because they are shown as Basic or maybe the Program Stage uses a Custom Form. However, a form is better displayed in Android as a section, that is the reason behind this warning

```
ERROR  2021-10-14 13:27:24,617  Indicators use dataElements not included in the package: ['iU2fkyo1R2k']
```
This could mean that the dataElement was not added to a correct dataElementGroup, or maybe the indicator should not be in the package and needs to be removed from the indicatorGroup

```
WARNING  2021-10-01 12:21:16,643  Data dimension in analytics use indicators not included in the package: ['AYQouZaqNQe', 'ijNR3ziiOnK', 'nSpKETGSOla', 'MJ6kzZQVUPN', 'PkMIm52Iohi']... Adding them
```
There is one or more dashboard item(s) (visualization, event report... ) using a series of indicators which are not included in the package. In this case, the script kindly adds them to the package but the Implementer should investigate whether these indicators need to be added to the package indicatorGroup or maybe the dashboard includes an item which do not belong there
```
ERROR  2021-10-21 15:35:35,361  Program rules use dataElements not included in the program: ['WUquHs0Al7h', 'SaCLndgg6On', 'ABhkInP0wGY', 'cCQRaVSSOsY', 'RTA1VXtS6r1'] [package_exporter:1493]
* INFO  2021-10-21 15:35:35,430  dataElement with WUquHs0Al7h : GEN - Birth weight (grams) [package_exporter:666]
* INFO  2021-10-21 15:35:35,430     Used in programRuleVariable with FWdLz0CUqYw : birth_weight [package_exporter:679]
* INFO  2021-10-21 15:35:35,430     Used in programRuleAction with kgU3X3htyqz [package_exporter:690]
* INFO  2021-10-21 15:35:35,431     Used in programRule with U3FeVKEw1Sr : Val: High birth weight > 10000g 
```
The implementer should verify the program rule and, if it is correct, add the dataElement to the package dataElementGroup
