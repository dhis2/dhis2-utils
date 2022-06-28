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


# Usage

Positional arguments (mandatory)

**1) Package Type or hardcoded UIDs separated by commas**
This parameter can be one UID or multiple UIDs separated by commas of a program(s), dataSet(s), dashboard(s) to package

OR

AGG -> Package aggregate dataSets fetching those with a code prefixed as specified in package\_prefix parameter
TRK -> Package tracker programs fetching those with a code prefixed as specified in package\_prefix  parameter
EVT -> Package event programs fetching those with a code prefixed as specified in package\_prefix  parameter
DSH -> Package dashboards fetching those with a code prefixed as specified in package\_prefix  parameter
GEN -> Package only GEN (generic) metadata

**2) Package prefix (resource code)**
The prefix which will be used by the script to scan the metadata codes and link the metadata which needs to be packaged and cannot be linked using DHIS2 existing references.

**3) Package code**
The DHIS2 code to be used for this package

Optional arguments

`  `-h, --help            show the help

`  `-i INSTANCE,        --instance INSTANCE

`                        `instance to extract the package from (robot account is required or add your own credentials in auth.json)

`  `-desc DESCRIPTION,  --description DESCRIPTION

`                        `Description of the package or any comments you want to add



Examples

python package\_exporter.py M3xtLkYBlKI MAL\_FOCI MLS0FI  -i=https://metadata.dhis2.org -desc="Fix for dashboards"

Equivalent to the command below, since MAL FOCI tracker package (MLS0FI) only comprises one program.
```
python package\_exporter.py TRK MAL\_FOCI MLS0FI -i=https://metadata.dhis2.org -desc="Fix for dashboards"
```
—--
```
python package\_exporter.py dr4Gf7GFjPx,HT62Jkl8dVx MAL MLCS00 -i=https://metadata.dhis2.org -desc="Fix for dashboards"
```
Since dr4Gf7GFjPx,HT62Jkl8dVx are the UIDs of 2 different dataSets, the script will package those and all related metadata as if it was an AGG package type. Hardcoded list of UIDs do not support mixing different metadata types, for example 1 dataSet + 1 program

—--
```
python package\_exporter.py SSLpOM0r1U7 EPI\_EIR EPIR00 -desc="Patch" -i=https://metadata.dhis2.org/tracker\_dev
```
—--
```
python package\_exporter.py AGG CH\_ADO CHADO0 -desc="First package release" -i=https://metadata.dhis2.org/dev
```
# Packaging strategy
The script uses the so-called “package prefix” (also called “resource code”) to match metadata which needs to be packaged. It does so by looking at the code field of the metadata resource and looking at whether it is prefixed by the package prefix and followed by any sequence of characters (including the empty sequence) after the package prefix. This enables packaging entire complete packages and also subpackages.

For example, the whole Malaria tracker package can be packaged by specifying ML as the package prefix, since the program code is MLS0… But to package Malaria Case Surveillance we would use MLS0CS… and for the Malaria Foci subpackage it would be MLS0FI. Let’s look at an example in the form of an API call:

<instance\_URL>/api/programs.json?filter=code:$like:ML&fields=name,code

code:$like:ML makes sure to get only the metadata whose code starts with ML. We get this:

![Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 001](https://user-images.githubusercontent.com/5999135/176217269-269f880e-3db5-4415-b625-85b95f23ed59.png)

As expected, we see that both tracker programs are retrieved so, by specifying ML (or MLS0) as package prefix (second positional mandatory parameter) we will include both tracker programs in a complete Malaria package. If we would like to package just Malaria CS, we would use MLS0CS as the package prefix.

<https://metadata.dev.dhis2.org/tracker_dev/api/programs.json?filter=code:$like:MLS0CS&fields=name,code>

![Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 002](https://user-images.githubusercontent.com/5999135/176217468-23035f3d-1d74-42c6-8672-6849699a4acf.png)

In other words. Generic Malaria metadata which needs to be included in the complete package should be prefixed ML\*\*\*\*, being \* any character or text. These characters in the package prefix can be used to specify metadata which belongs to a Malaria subpackage.

Now the question is… What metadata is packaged based on a “package prefix”? It will depend on the package type, but generally speaking the following metadata types will be packaged by looking at their codes and matching them with the package prefix:

- userGroups
- dashboards
- dataElementGroups
- indicatorGroups
- predictorGroups
- validationRuleGroups
- documents

And what about the other metadata?

The following metadata is packaged when being assigned to the corresponding group:

- dataElements FROM dataElementGroups
- indicators FROM indicatorGroups
- predictorGroups FROM predictorGroups
- validationRules FROM validationRuleGroups

Coming back to the example of MAL CS Malaria, looking at the dataElementGroups with a package prefix MLS0CS the script will fetch the following dataElementGroup and will package all the dataElements included in it:
![Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 003](https://user-images.githubusercontent.com/5999135/176217625-1d311c16-9ad3-40c0-bfed-d3e957f69142.png)
When packaging metadata which is grouped, the script will check references which may have been omitted by the implementer but need to be included. In some cases it will warn the user that it is automatically adding a reference or it will give an error, exiting with code 1.

An example of this logic for a tracker package:

Get the dataElementGroup whose code matches the package prefix

From the dataElementGroup, get all dataElements (DEs) to include in the package
Check for DEs used in the Program Stage(s) of the program… Anything missing?

Check for DEs used in Program Rules (via PRV or PRA)... Anything missing?

Check for DEs used in Indicators and Program Indicators... Anything missing?

Check for DEs used in a dashboard item... Anything missing?

Etc…

And what about the rest of the metadata? Most of the metadata to be packaged comes from nested references, i.e. a reference to another metadata object from within a metadata object. A good example is a program. From a program we can infer the trackedEntityAttributes, trackedEntityType, programIndicators, programRuleVariables, programRules, programStages and programSections. There are nested references which are also packaged by the script as it can be seen in the image below, which depicts how the script processes and packages the TEAs used in the TET used in a program. Similarly, from the programStages we can get the programStageSections to package, from the programRules we get the programRuleActions to package, etc…

![Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 004](https://user-images.githubusercontent.com/5999135/176217721-0876095f-08d5-44d2-8399-aa27698a7ac5.png)

Another example would be optionSets, options… Which are inferred from the corresponding TEAs and DEs.

![Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 005](https://user-images.githubusercontent.com/5999135/176217747-8545fdde-bd91-45e1-b818-0e95a5c81d8b.png)

An interesting case which involves nested references and reference cleanup would be that of disaggregations specified in the form of categories, category options, category combos, category option combos )COC). To simplify, let’s say a categoryCombo can be assigned to a dataElement (there are categoryCombos (CCs) also used in dataSets, programs, etc… The script will process all of them). From a CC, we can get all the other references to categories, COCs and category options. For example, if we look at the following dataElement, we see it has a CC Adults/Sex/Conditions:

![Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 006](https://user-images.githubusercontent.com/5999135/176217784-6f5d5a01-2656-4e1c-b9d5-51c4bcf981d0.png)

In the json payload we can see in green the metadata references which will be kept (because they refer to a metadata that is part of the package) and in orange those which will be excluded. Let’s look at this example in more detail; this categoryCombo ( Adults/Sex/Conditions) involves 3 categories that are packaged:

![Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 007](https://user-images.githubusercontent.com/5999135/176217848-a1c29ebc-c5b0-4116-a2d0-bba8713b7b91.png)

But these categories may reference other categoryCombos which are not part of this package and need to be cleaned up:

![Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 008](https://user-images.githubusercontent.com/5999135/176217906-d2102c9e-e185-44a5-a9b8-7bcf99f9d717.png)

And in turn, each category references category options which need to be included in the package but we need to clean unnecessary categories references, i.e. references in a category option to a category which is outside of the 3 we are packaging as part of this CC:

![Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 009](https://user-images.githubusercontent.com/5999135/176217951-ecd01685-6bb5-468b-92ee-a004f8acd319.png)
## Hardcoded references
Not everything in the DHIS2 universe is referenced through a key “id” in the json object. The script also scans numerator and denominator expressions, filters and expressions of program indicators, predictor operations, programRule conditions… trying to find references which also need to be included in the package. Some examples here below:

![Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 010](https://user-images.githubusercontent.com/5999135/176218004-c77a213b-4720-4715-a174-f7decdfd5152.png)

![Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 011](https://user-images.githubusercontent.com/5999135/176218057-f3abe1dd-5cf3-4f4e-9d74-4550e88de5b0.png)

It is worth noticing that this process of including hardcoded references will trigger the corresponding processes of searching for nested references and cleaning unnecessary references. For example, from OUG{dywujBsfIew} we decide to include in the package the OUG corresponding to that UID which is “Districts”:

![Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 012](https://user-images.githubusercontent.com/5999135/176218110-8a53e48c-c161-4e14-8d3f-12deb4d954a3.png)

The script will remove the organisationUnits as they are not supposed to be packaged.

The script will include the organisationUnitGroupSets specified in groupSets list.

The script will trim the organisationUnitGroupSets to remove the OUG which doesn't belong to the package.

The script will warn the user that a OUG has been included so this is documented in the installation guide and users are aware that they need to map this OUG to something equivalent in their instance.
## Predefined references
Some metadata is included by default in the package, i.e. it is always included. At present, this involves:

user 
`	`vUeLeQMSwhN	package_admin

attributes

iehcXLBKVWM	Code (ICD-10)

mpXON5igCG1	Code (Loinc)

I6u65yRc0ct	Code SNOMED

vudyDP7jUy5	Data element for aggregate data export
## Sharing properties
All the metadata packages have a minimum of 3 user groups: data capture, access and admin.

The standard sharing is as follows:


||dataSets|dashboards|programs/programStages|
| :- | :- | :- | :- |
|Data Capture|<p>data: rw</p><p>metadata: r</p>|<p>data: r</p><p>metadata: r</p>|<p>data: rw</p><p>metadata: r</p>|
|Access|data: r<br>metadata: r|data: r<br>metadata: r|data: r<br>metadata: r|
|Admin|data: none<br>metadata: rw|data: none<br>metadata: rw|data: none<br>metadata: rw|

The script will warn the user if the sharing hasn’t been done according to the metadata packages standards and will try to correct it whenever is possible. For this, the script is going to scan the different userGroup codes and will try to find the keyword DATA, ACCESS or ADMIN.
## Placeholder replacement
The script may replace some UID references in certain cases with a placeholder which needs to be replaced with a UID in the target instance where we want to import the package. It will also warn the user to make sure these specific cases are documented in the installation guide. The users will have to replace these placeholders with the corresponding UID of that metadata object in their system.

**ROOT UIDs in dashboard items (**<OU\_ROOT\_UID>**)**

Some visualizations require an organisation unit to work, so this reference cannot be simply removed.

![Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 013](https://user-images.githubusercontent.com/5999135/176218229-6948215d-88be-4fc3-958b-dd0fa8c37e45.png)

In this scenario, the script will show this message to the user:

\* WARNING Element b2BCsoCcnbZ has root OU assigned to it (IWp9dQGM0bS)... Replacing with placeholder: **<OU\_ROOT\_UID>**

And when we check the visualization, we find this:

![Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 014](https://user-images.githubusercontent.com/5999135/176218282-b18f2b9a-41a6-43b3-bf70-e7041cc2fff5.png)

<OU\_ROOT\_UID> needs to be replaced with the UID of the root OU in the target system OU hierarchy **prior to importing** the package.

**Organisation Unit Levels in PREDICTORs (**<OU\_LEVEL\_-OULName-\_UID>**)**

We can find that an Organisation Unit Level (OUL) is referenced in the predictors as follows:

![Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 015](https://user-images.githubusercontent.com/5999135/176218339-b2689e7d-db31-4874-84fc-e32ef59674f2.png)

The script will check the name of the OUL and will replace the UID with a placeholder <OU\_LEVEL\_-OULName-\_UID> as it can be seen below, in the final package exported:

![Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 016](https://user-images.githubusercontent.com/5999135/176218375-88ae3843-9289-4ae3-bae1-ec67c28bb269.png)
## Cleaning unnecessary fields in the metadata
Currently the following metadata fields are removed from each metadata element (if present) in the package:

lastUpdated
lastUpdatedBy
created
createdBy
href
access
favorites
allItems
displayName
displayFormName
displayShortName
displayDenominatorDescription
displayNumeratorDescription
displayDescription
interpretations

The goal removing these fields is to compress and reduce the amount of information included in the package and making sure that only the crucial metadata fields are packaged. For example, href does not add any value since it refers to the URL where the metadata was stored. Same goes for the user who created or updated the metadata, it does not add any useful information to the users installing the package. In other cases like those of displayXXX fields, they are auto generated by DHIS2 when importing the package based on the locale of the target system where the package is imported.

Also, organisation units assignments are removed with the exception of when they are replaced with a placeholder.
## Cleaning unnecessary references
Previously we have already discussed some metadata nested packaging scenarios where removing references was necessary. Let’s look at a practical example: looking back at the example of the Malaria package, when we check the available dataElementGroups (DEG) for ML package prefix, we get this:

![Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 017](https://user-images.githubusercontent.com/5999135/176218444-587736c7-a5a2-43bb-9a02-5c7c797a2f8b.png)

There is one DEG for each subpackage, Malaria CS and Malaria FOCI.

When the user specifies ML as package prefix, both DEGs are included in the package as well as their corresponding DEs. However, DEs included in both DEG are not included twice. The script performs a merge of both lists of DEs to come up with a list of unique DEs (no duplicates) and those are the final DEs packaged.

But what happens if we want to package only the Malaria CS package (MLS0CS) and there are DEs which belong to both DEGs Malaria CS and Malaria FOCI? Let’s look at this dataElement:

![Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 018](https://user-images.githubusercontent.com/5999135/176218500-99fc889f-b93a-4b53-aa62-66188860afb7.png)

When packaging Malaria CS sub-package, if the script add this dataElement as it is, the reference to the DEG MLS0FI will be included in the package and the package will fail to import, since this DEG won’t be part of this sub-package (its code is MLS0FI, not MLS0CS) . To avoid this issue, the script removes unnecessary references when packaging, as we can see in the final json file:

![Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 019](https://user-images.githubusercontent.com/5999135/176218543-0cf12685-39fd-4470-bc0c-ef135fa02680.png)

However, if we look at the same DE in the complete Malaria package (including CS and FOCI), both DEG are included as expected.

![Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 020](https://user-images.githubusercontent.com/5999135/176218584-15be4eeb-2daa-4f65-ae88-c20d46e17c1f.png)

## **Types of packages**
###
### TRK package
Packages including tracker programs with programType = WITH\_REGISTRATION

### EVT package
Packages including event programs with programType = WITHOUT\_REGISTRATION

### AGG package
Packages including dataSets used to collect aggregate data.
### GEN Package
The GEN Package packages the following metadata by looking at the codes of the following metadata types:

- dataElementGroups
- indicatorGroups
- indicatorTypes
- categoryOptionGroups
- trackedEntityTypes

The main difference with the previous package types are:
It looks for GEN in the code of categoryOptionGroups to decide what category options are included in the package (references to categories, categoryCombos or categoryOptionCombos are removed)
It looks for a particular trackedEntityType GEN to package the different GEN trackedEntityAttributes. In this case, this TET acts as a TEA group and it won’t make it to the final package, only the TEAs referenced by it.
### DASHBOARD (DSH) package
The idea behind a dashboard package is that the country/user is already collecting data with their data elements/datasets/categories which are already configured but they would like to use the dashboard to standardize the analytic outputs. The user will install the dashboards in the package and proceed to map their data elements or categories to the indicators or category options groups that are configured on the dashboard items, making it possible to have the visualizations in a standard way without having to use the complete package (AGG)

The DSH package will package the following metadata using package prefix codes:

- userGroups
- indicatorGroups
- dashboards

It also manipulates the indicators:

- It replaces numerator and denominator expressions with a value 1
- It prefixes every indicator name with “[CONFIG]” to point to the users that these indicators need to be configured and mapped to their current metadata

## Summary of metadata packaging per type
The following table shows all metadata types which are currently packaged ordered as they are processed by the script.



|**Metadata type**|**TRK**|**EVT**|**AGG**|**DSH**|**GEN**|
| :- | :- | :- | :- | :- | :- |
|userGroups|Package prefix in code|Package prefix in code|Package prefix in code|Package prefix in code||
|users|Predefined|Predefined|Predefined|Predefined||
|dashboards|Package prefix in code|Package prefix in code|Package prefix in code|PARAMETER||
|eventCharts|From dashboard|From dashboard|From dashboard|From dashboard||
|eventReports|From dashboard|From dashboard|From dashboard|From dashboard||
|maps|From dashboard|From dashboard|From dashboard|From dashboard||
|visualizations|From dashboard|From dashboard|From dashboard|From dashboard||
|programRules|From programs|From programs||||
|programRuleActions|From programRules|From programRules||||
|programRuleVariables|From programs|From programs||||
|indicatorGroups|Package prefix in code|Package prefix in code|Package prefix in code|Package prefix in code|Package prefix in code|
|indicators|From indicatorGroups|From indicatorGroups|From indicatorGroups|From indicatorGroups|From indicatorGroups|
|indicatorGroupSets|From indicatorGroups|From indicatorGroups|From indicatorGroups|From indicatorGroups||
|indicatorTypes|From indicators|From indicators|From indicators|From indicators|Package prefix in code|
|organisationUnitGroups|Hardcoded|Hardcoded|Hardcoded|Hardcoded||
|organisationUnitGroupSets|From organisationUnitGroups|From organisationUnitGroups|From organisationUnitGroups|From organisationUnitGroups||
|programIndicators|From programs|From programs||||
|programIndicatorGroups|From programIndicators|From programIndicators||||
|programSections|From programs|From programs||||
|programStages|From programs|From programs||||
|programStageSections|From programStages|From programStages||||
|programs|PARAMETER|PARAMETER||||
|programNotificationTemplates|From programs, programStages|From programs, programStages||||
|trackedEntityInstanceFilters|From programs|||||
|trackedEntityTypes|From programs||||Package prefix in code|
|trackedEntityAttributes|From programs, trackedEntityInstances||||From GEN trackedEntityType|
|predictorGroups|Package prefix in code|Package prefix in code|Package prefix in code|||
|predictors|From predictorGroups|From predictorGroups|From predictorGroups|||
|jobConfigurations|jobType:eq:PREDICTOR|jobType:eq:PREDICTOR|jobType:eq:PREDICTOR|||
|validationNotificationTemplates|From validationRules|From validationRules|From validationRules|||
|validationRuleGroups|Package prefix in code|Package prefix in code|Package prefix in code|||
|validationRules|From validationRuleGroups|From validationRuleGroups|From validationRuleGroups|||
|dataElementGroups|Package prefix in code|Package prefix in code|Package prefix in code||Package prefix in code|
|dataElements|From dataElementGroups|From dataElementGroups|From dataElementGroups||From dataElementGroups|
|dataSets|Package prefix in code|Package prefix in code|PARAMETER|||
|sections|From dataSets|From dataSets|From dataSets|||
|dataEntryForms|From programStages, dataSets1|From dataSets1|From dataSets|||
|attributes|Predefined|Predefined|Predefined|||
|documents|Package prefix in code|Package prefix in code|Package prefix in code|||
|reports|Package prefix in code|Package prefix in code|Package prefix in code|||
|sqlViews|Package prefix in code|Package prefix in code|Package prefix in code|||
|constants|Hardcoded|Hardcoded|Hardcoded|||
|optionSets|From dataElements, trackedEntityAttributes|From dataElements, trackedEntityAttributes|From dataElements, trackedEntityAttributes|||
|options|From optionSets|From optionSets|From optionSets|||
|optionGroups|From optionSets, PRAs|From optionSets, PRAs|From optionSets|||
|legendSets|From visualizations, maps, programIndicators, trackedEntityAttributes, dataSets, indicators, optionGroups|From visualizations, maps, programIndicators, trackedEntityAttributes, dataSets, indicators, optionGroups|From visualizations, maps, programIndicators, trackedEntityAttributes, dataSets, indicators, optionGroups|From visualizations, maps||
|categoryCombos|default, from dataSets, dataElements|default, from dataSets, dataElements, programs|default, from dataSets, dataElements|||
|categoryOptionCombos|default, from categoryCombos|default, from categoryCombos|default, from categoryCombos|||
|categories|default, from categoryCombos|default, from categoryCombos|default, from categoryCombos|||
|categoryOptions|default, from categories|default, from categories|default, from categories||From categoryOptionGroups|
|categoryOptionGroups|From categoryOptions,visualizations|From categoryOptions,visualizations|From categoryOptions,visualizations|From visualizations|Package prefix in code|
|categoryOptionGroupSets|From categoryOptionGroups|From categoryOptionGroups|From categoryOptionGroups|From categoryOptionGroups||

1 Some tracker programs, like HIV CS, also contain a dataSet which needs to be included in the package
## The package label
The exported package always includes a package label with the following fields:

- **DHIS2Build**: DHIS2 build of the instance from where the package is exported
- **DHIS2Version**: DHIS2 version of the instance from where the package is exported
- **code**: package code (positional parameter)
- **description**: package description (parameter -desc)
- **lastUpdated**: timestamp of the metadata object in the package with the most recent last updated timestamp
- **locale**: en/fr/es/pt. Language used for the metadata in the package
- **name**: package\_code + '\_' + package\_type + '\_' + package\_version + '\_DHIS' + dhis2\_version + '-' + locale
- **type**: AGG / TRK / EVT / DSH / GEN (positional parameter or extracted)
- **version**: version of the package in the format x.y.z (parameter -v)

<img width="284" alt="Aspose Words 4a6a7042-ece5-4988-8a5d-4d9fa9a5666c 021" src="https://user-images.githubusercontent.com/5999135/176218672-82675534-777d-4935-b028-000779317fe8.png">

## Package DHIS2 version
A metadata package has 2 different versions attached to it:

- The package version: the version of the package will change as the package is developed, corrections are made and new functionality is added to the metadata contained in the package.
- The DHIS2 version: this is the DHIS2 version with which the package is compatible. The DHIS2 version of the package is determined by the instance where the package is living and where it is exported.

The metadata packages team normally carries out the package development in instances which are 2 versions behind the latest official DHIS2 version released. Thus, in order to be able to generate the package in higher versions of DHIS2 we need to copy the target dev instance in a new one and perform an upgrade. Only then we can use the script to obtain a compatible package. Exporting packages in different DHIS2 versions can be critical, since metadata might experience changes which are not backwards compatible. For example, from 2.33 to 2.34 the metadata types “charts” and “eventReports” ceased to exist and were integrated in the metadata type “visualizations”
# Warning and Error summary
The difference between warnings and errors is that an error will either stop the execution of the script or will prevent the package from being generated but the warning not. An error reflects a situation which has been identified as problematic for the package generation, thus an error will force users to take an action. A warning might also require the user to take some actions but the script can take an action to temporarily solve the problem and export a valid standalone package. 


|**Type**|**Message**|**Action**|
| :- | :- | :- |
|WARNING|Group (UID) contains elements which do NOT belong to the package :|Remove them from the group|
|WARNING|programIndicatorGroup UID has programIndicators which belong to multiple programs :||
|WARNING|Element UID has write public access||
|WARNING|Element UID has wrong user|Replace with WHOAdmin|
|WARNING|Element UID is shared with wrong/specific users|Remove the sharing|
|WARNING|ElementUID is shared with a User Group(s) outside the package|Remove the userGroup from sharing|
|WARNING|More than one OU root found in OU Tree|*Relates to replacing the root OU in with a placeholder*|
|WARNING|The dashboard item with UID has organisation units assigned|Remove organisationUnits|
|WARNING|Element UID has root OU assigned to it (OU\_ROOT\_UID)|Replace with placeholder|
|WARNING|There are org units assigned|Remove organisationUnits|
|WARNING|The program has X eventReports assigned to it, but onlyY were found in the dashboards belonging to the program||
|WARNING|Indicators use programIndicators not included in the program:||
|WARNING|Data dimension in analytics use programIndicators not included in the package|Add the PIs to the package|
|WARNING|There are programNotificationTemplates with package prefix XX not used in any program rule action or program||
|WARNING|ProgramNotificationTemplates use a userGroup recipient not included in the package|Add the userGroup to the package|
|WARNING|dataSet use a userGroup recipient not included in the package|Add the userGroup to the package|
|WARNING|COC Elements used in dataEntryForm are not part of the package||
|WARNING|DataElements assigned to the Program Stage(s) in package: are not assigned to any dataElementGroup|Add the DEs to the package|
|WARNING|Program stage use dataElements not assigned to any programStageSection:||
|WARNING|DataElements assigned to the DataSet(s) in package: are not assigned to any dataElementGroup|Add the DEs to the package|
|WARNING|Indicators use dataElements not included in the package:|Add the DEs to the package|
|WARNING|Predictors use dataElements not included in the package:|Add the DEs to the package|
|WARNING|Data dimension in analytics use dataElements not included in the package:|Add the DEs to the package|
|WARNING|Data dimension in analytics use indicators not included in the package:|Add the Indicators to the package|
|WARNING|DataSets use indicators not included in the package:|Add the Indicators to the package|
|WARNING|There are interpretations|Remove|
|WARNING|Tracked Entity Type has TEAs not used in the program:|Add te TEAs to the package|
|WARNING|Option Group references optionSet which don't belong in the package||
|ERROR|The parameters XX returned no result for programs / dataSets / dashboards|Parameters passed to the script are probably not correct, stop execution|
|ERROR|Version provided XXX does not match format X.Y.Z|Stop execution|
|ERROR|Program rules use trackedEntityAttributes not assigned to the program:|No package is generated|
|ERROR|Program indicators use trackedEntityAttributes not included in the program:|No package is generated|
|ERROR|Indicators use trackedEntityAttributes not included in the program:|No package is generated|
|ERROR|Predictors use programIndicators not included in the program|No package is generated|
|ERROR|Program stage sections use dataElements not assigned to any programStage:|No package is generated|
|ERROR|Program rules use dataElements not included in the program:|No package is generated|
|ERROR|Program indicators use dataElements not included in the package:|No package is generated|
|ERROR|Validation rules use dataElements not included in the program:|No package is generated|

# Log examples
**Example 1**

WARNING  2021-10-25 17:58:23,378  Program stage use dataElements not assigned to any programStageSection: ['xMkkGCwSaDK', 'cNA9EmFaiAa', 'J0dqTnGzX6T', 'HGjbAPoyEBu', 'Y3eDHMTcSYk', 'OWolh3WKA3Q', 'knh2BOb3F0I', 'NxVIX3mIhGt']

DataElements may not be assigned to a section because they are shown as Basic or maybe the Program Stage uses a Custom Form. However, a form is better displayed in Android as a section, that is the reason behind this warning

**Example 2**

ERROR  2021-10-14 13:27:24,617  Indicators use dataElements not included in the package: ['iU2fkyo1R2k']


This could mean that the dataElement was not added to a correct dataElementGroup, or maybe the indicator should not be in the package and needs to be removed from the indicatorGroup

**Example 3**

WARNING  2021-10-01 12:21:16,643  Data dimension in analytics use indicators not included in the package: ['AYQouZaqNQe', 'ijNR3ziiOnK', 'nSpKETGSOla', 'MJ6kzZQVUPN', 'PkMIm52Iohi']... Adding them


There is one or more dashboard item(s) (visualization, event report... ) using a series of indicators which are not included in the package. In this case, the script kindly adds them to the package but the Implementer should investigate whether these indicators need to be added to the package indicatorGroup or maybe the dashboard includes an item which do not belong there

**Example 4**

ERROR  2021-10-21 15:35:35,361  Program rules use dataElements not included in the program: ['WUquHs0Al7h', 'SaCLndgg6On', 'ABhkInP0wGY', 'cCQRaVSSOsY', 'RTA1VXtS6r1'] [package\_exporter:1493]

\* INFO  2021-10-21 15:35:35,430  dataElement with WUquHs0Al7h : GEN - Birth weight (grams) [package\_exporter:666]

\* INFO  2021-10-21 15:35:35,430     Used in programRuleVariable with FWdLz0CUqYw : birth\_weight [package\_exporter:679]

\* INFO  2021-10-21 15:35:35,430     Used in programRuleAction with kgU3X3htyqz [package\_exporter:690]

\* INFO  2021-10-21 15:35:35,431     Used in programRule with U3FeVKEw1Sr : Val: High birth weight > 10000g 


The implementer should verify the program rule and, if it is correct, add the dataElement to the package dataElementGroup
