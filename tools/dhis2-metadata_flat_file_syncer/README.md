# Metadata Flat File Syncer

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install required packages.

```bash
pip install -r requirements.txt
```

Configure instances.conf with the URLs of your working instances where metadata will be imported/exported
You will need to create a Google API Key json token:
You will need to create a Google API Key json token:
1. Go to the API Console in Google Cloud: [https://console.developers.google.com/](https://console.developers.google.com/)

   <img src="https://github.com/dhis2/dhis2-utils/assets/5999135/b37c3d63-971a-47ef-8efc-27964e991247" style="width: 50%; height: auto;"/>

2. From the projects list, select a project or create a new one.

   <img src="https://github.com/dhis2/dhis2-utils/assets/5999135/41039838-979a-4b21-a272-63fa0310d063" style="width: 100%; height: auto;"/>
   
   <img src="https://github.com/dhis2/dhis2-utils/assets/5999135/04d13e0a-8d57-4f6f-ab51-0b9f200d4473" style="width: 50%; height: auto;"/>

3. The message "You don’t have any APIs available to use yet. To get started, click “Enable APIs and services” or go to the API library"

4. Enable Google Drive API and Google Spreadsheets API

   <img src="https://github.com/dhis2/dhis2-utils/assets/5999135/c296b505-d45e-489d-8e16-a0d442295d1f" style="width: 50%; height: auto;"/>

5. Click on Create Credentials

   <img src="https://github.com/dhis2/dhis2-utils/assets/5999135/f713107f-dc38-488d-bb19-e9b640dc84e1" style="width: 70%; height: auto;"/>

6. In Credential Type, select Application data and click on NEXT

   <img src="https://github.com/dhis2/dhis2-utils/assets/5999135/a4a26e0f-58ae-4f57-a674-e9830e3e018f" style="width: 50%; height: auto;"/>

7. In Service account details, choose a name for the account and click on CREATE AND CONTINUE

   <img src="https://github.com/dhis2/dhis2-utils/assets/5999135/f2b73c7d-b642-4e7e-a579-c2ace75a1279" style="width: 50%; height: auto;"/>

8. On the left menu, select Credentials and then select the Service Account which was created

   <img src="https://github.com/dhis2/dhis2-utils/assets/5999135/0eb7e78b-6c75-4fdf-bdef-b0bda54f2f8e" style="width: 90%; height: auto;"/>

9. Select KEYS on the top menu and then click on ADD KEY

<img src="https://github.com/dhis2/dhis2-utils/assets/5999135/81813249-2c07-41a4-b40a-9b6e23765f49" style="width: 50%; height: auto;"/>

10. Select JSON key type

<img src="https://github.com/dhis2/dhis2-utils/assets/5999135/8d3a6af1-18f9-45f7-b9d7-3519228f0aeb" style="width: 50%; height: auto;"/>

11. The google private key is saved in your computer as a json file

<img src="https://github.com/dhis2/dhis2-utils/assets/5999135/e9c4e66d-fbfc-424a-b6b8-6a9920608530" style="width: 35%; height: auto;"/>


## Usage

You can run the backend using the following command (it will use metadata_types.conf). Parameter -a, -auth is a mandatory parameter used to provide the Google API Key.
```bash
python metadata_ff_syncer.py -a google_private_key.json
```

If you want to use a different conf file, you can use parameter -c, -conf:
```bash
python metadata_ff_syncer.py -a google_private_key.json -c my_configuration.conf
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

## Troubleshooting

On Windows systems, when executing
```
pip install -r requirements.txt
```
you could encounter an ERROR during the installation of the numpy==1.23.4 library. As a workaround, consider modifying the "requirements.txt" file. Locate the line with numpy==1.23.4 and replace it with simply numpy. This adjustment will prompt pip to install the most recent version of the library, addressing the encountered ERROR. You may also need to upgrade packages that with dependencies on numpy, such as pandas and gspread-dataframe.
It's important to note that the Flat File tool hasn't undergone comprehensive testing with the latest version, although no issues have been reported thus far. 
