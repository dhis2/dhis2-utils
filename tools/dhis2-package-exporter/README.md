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

positional arguments:
  program_uid           the id of the program to use
  health_area           the health_area of the package, e.g. HIV, TB, EPI, COVID19
  intervention          the intervention, formerly the package prefix, i.e. CS, EIR, etc..

optional arguments:
  -h, --help            show this help message and exit
  -v PACKAGE_VERSION, --version PACKAGE_VERSION
                        the package version to use
  -i INSTANCE, --instance INSTANCE
                        instance to extract the package from (robot account is required!) - tracker_dev byu default
  -desc DESCRIPTION, --description DESCRIPTION
                        Description of the package or any comments you want to add

Examples:


```bash
python package_exporter.py M3xtLkYBlKI MAL FOCI -v=1.0.1 -i=https://who.sandbox.dhis2.org/tracker_dev234 -desc="Fix for dashboards"

python package_exporter.py Xh88p1nyefp HIV CS -v=1.0.1
```



