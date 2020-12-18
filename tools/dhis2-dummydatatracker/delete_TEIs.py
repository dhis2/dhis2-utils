
from dhis2 import Api, RequestException, setup_logger, logger #make sure you have dhis2.py installed, otherwise run "pip3 install dhis2.py"

api = Api('https://who-dev.dhis2.org/tracker_dev', 'Manu', '')

setup_logger()

user = 'robot'


def main():

    logger.warning("Server source running DHIS2 version {} revision {}".format(api.version, api.revision))

    params = {
        'ou': 'GD7TowwI46c', # GD7TowwI46c
        'ouMode': 'DESCENDANTS',
        'program': 'Xh88p1nyefp',
        'skipPaging': 'true',
        #'lastUpdatedDuration': '4d',
        #'fields': '*'
        'fields': 'trackedEntityInstance'
    }

    data = api.get('trackedEntityInstances', params=params).json()['trackedEntityInstances']

    logger.info("Found " + str(len(data)) + " TEIs")

    user = 'robot'
    for tei in data:
        # Uncomment this to filter by user
        # if tei["enrollments"][0]["storedBy"] != user:
        #     logger.warning("Skipping tei stored by " + tei["enrollments"][0]["storedBy"])
        #     continue
        tei_uid = tei['trackedEntityInstance']
        try:
            response = api.delete('trackedEntityInstances/' + tei_uid)
        except RequestException as e:
            logger.error(e)
            pass
        else:
            logger.info("TEI " + tei_uid + " removed")


if __name__ == '__main__':
    main()