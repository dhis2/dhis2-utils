# DHIS2 ORG UNIT GENERATOR

A command line tool to generate Org Unit hierarchies for DHIS2 testing.
The generated org units are sent directly to the metadata endpoint for import in batches.

## Requirements

Python3

## Set up the environment

```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```
## Run

###  options

#### optional

- `-h` `--help` display usage info
- `-u` `--user` DHIS2 instance user (default=`admin`)
- `-p` `--password` DHIS2 instance password (default=`district`)
- `-l` `--levels` Levels in Org Unit hierarchy (default=6, max=7)
- `-k` `--kids` Number of child OUs (kids) as each level (default=10, max=26)
- `-c` `--coords` Rectangle defining the outer Org Unit boundary (default= 10 10 10 10)
    --coords X Y DX DY, where
    - X=latitude offset in degrees
    - Y=Longitude offest in degrees
    - DX=width along longitude in degrees
    - DY=height along latitude in degrees
- `-b` `--batch` Batch size for POSTs to the importer (default=1000)
- `-e` `--estimate` Just display estimated number of OUs and exit.

#### mandatory

- `-s` `--server` DHIS2 instance url


Examples:

```
# generate OUs seven levels deep, with three sub-units per level
python3 orgenerator.py -s https://test.performance32.dhis2.org/phil  -l 7 -k 3


# generate OUs five layers deep, with 26 sub-units per level
# POST in batches of 500
# with outer boundary rectangle starting at 20deg long., 15deg lat., and extending 10deg East, 5 North.
python3 orgenerator.py -s https://test.performance32.dhis2.org/phil  -l 5 -b 500 --coords 20 15 10 5

```


> **NOTE**
>
> The amount of org units is calculated as: kids^^(levels-1) + kids^^(levels-2) + ... + kids^0
