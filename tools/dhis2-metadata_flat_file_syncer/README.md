# Metadata Flat File Syncer

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install required packages.

```bash
pip install -r requirements.txt
```

Configure instances.conf with the URLs of your working instances where metadata will be imported/exported
You will need to create a Google API Key as documented [here](https://support.google.com/googleapi/answer/6158862?hl=en)

## Usage

You can run the backend using the following command (it will use metadata_types.conf). Parameter -a, -auth is a mandatory parameter used to provide the Google API Key.
```bash
python metadata_ff_syncer.py -a google_auth_file.json
```

If you want to use a different conf file, you can use parameter -c, -conf:
```bash
python metadata_ff_syncer.py -a google_auth_file.json -c my_configuration.conf
```

Once the backend is running, please open templates/index.html in Google Chrome or your preferred browser.

## Important notes

The tool allows managing the spreadsheets from the front end: you can open, delete or export the metadata existing in an instance to your spreadsheet.<br>
The tools also allows updating the instance from the current metadata configuration in your spreadsheet. 
Every time a new spreadsheet is created or updated, **the tool attempts to share it with your user if your email is configured for your dhis2 account**.<br>
The metadata types available in the selector are populated from metadata_types.conf -> If you need to work with less metadata_types, create your own custom version.<br>
For every metadata_type imported in the instance, **a json file is created** in the same folder to allow further investigation or sharing.<br>

- When importing metadata in an instance, **the order when selecting ALL comes from metadata_types.conf**, reading every line from top to bottom.<br>
- When exporting metadata to a flat file, the fields (columns) that will be exported are configured in metadata_types.conf. It is possible to redefine these fields by working with your own custom conf file.<br>
- When updating the metadata in an instance, **only the fields present in the spreadsheet will be updated or created**. For the case of metadata already existing in the instance which it is updated, the tool first GETs all owned fields and only updates those in the spreadsheet, preserving the rest. This means, for example, that if you just want to update an specific fields using a quick find and replace, you could just have id, shortName and name as columns. Even though some mandatory fields are missing, the tool will POST the json payload filling the gaps with the what is available in the instance.<br>

