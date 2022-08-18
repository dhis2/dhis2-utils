# dhis2-metadata-package-diff

Get differences between package files

## Tools for metadata diff

Python 3.6+ is required.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install required packages.

```bash
pip install -r requirements.txt
```


## Usage

Positional arguments:
```
package1.json	json file of previous package (older version) 
package2.json	json file of current package (latest version)
```
Examples:

```bash
python metadata_package_diff.py EIR_TRK_0.9.2_DHIS2.34-en.json EIR_TRK_1.0.2_DHIS2.34.7-EMBARGOED-en.json
```


## Output

Produces a csv file with the current date in the name, comparison_25-Oct-2021_16-33-45.csv. This file shows the metadata that has been DELETED, CREATED and UPDATED from one package to another.  
It also provide a json file package_diff_delete.json which can be imported with strategy DELETE to try to delete the metadata in instances where the old version of the package was installed