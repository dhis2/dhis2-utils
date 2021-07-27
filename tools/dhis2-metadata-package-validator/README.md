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

- `O-MQ-2`: Error. Expected sortOrder for options of an optionSet (starts at 1 and ends at the size of the list of options)
- `PR-ST-3`: Error. Program Rule without action
- `PRV-MQ-1`: More than one PRV with the same name


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

