# METADATA PACKAGE VALIDATOR

A command line tool to validate a metadata package.

## Requirements

Python 3.6+ is required.

## Run

### mandatory argument

- `-f` `--file` metadata package file path

### example

`metadata_package_validator.py -f AEFI_TRACKER.json`

## List of validations

- `DE-MQ-2`: DataElement contains the words 'number of'
- `DS-MQ-1`: Custom form in a dataset
- `DS-MQ-2`: Empty custom form in a dataset
- `I-MQ-3`: Indicator contains the word 'proportion' or 'percentage'
- `O-MQ-2`: Error. Expected sortOrder for options of an optionSet (starts at 1 and ends at the size of the list of options)
- `OG-MQ-1`: Error. All options present in the optionGroups MUST belong to an optionSet.
- `P-MQ-1`: Custom form in a program (enrollment)
- `P-MQ-2`: Empty custom form in a program (enrollment)
- `PI-MQ-3` - Program Indicator contains the word 'proportion' or 'percentage'
- `PR-ST-3`: Error. Program Rule without action
- `PR-ST-4`: Program Rule has a PR Action that uses a DE that does not belong to the associated program.
- `PR-ST-5`: Tracked Entity Attribute associated to a program rule action MUST belong to the program/TET that the program rule is associated to.
- `PRV-MQ-1`: More than one PRV with the same name in the same program
- `PRV-MQ-2`: The PRV contains unexpected characters
- `PS-MQ-1`: Custom form in a program stage
- `PS-MQ-2`: Empty custom form in a program stage
- `ALL-MQ-17`: Missed code field in a resource
- `ALL-MQ-18`: Codes MUST be upper case ASCII (alphabetic A-Z), and the symbols '_' (underscore), '-' (hyphen), '.' (dot), '|' (Bar o Pipe)
- `ALL-MQ-19`: Translation duplicated
- `ALL-MQ-20`: A resource (programIndicators, programRules, programRuleActions) contains a 'program_stage_name'
- `ALL-MQ-21`: Unexpected translation. Unexpected symbol in locale/Missing locale in translation



## Acronyms
- `DE` Data Element
- `DEG` Data Element Group
- `O` Option
- `OG` Option Group
- `I` Indicator
- `P` Program
- `PI` Program Indicator
- `PS` Program Stage
- `PSS` Program Stage Section
- `PSDE` Program Stage Data Element
- `PR` Program Rule
- `PRA` Program Rule Action 
- `PRV` Program Rule Variable
- `OU` Organisation Unit
- `TEA` Tracked Entity Attribute
- `TET` Tracked Entity Type

