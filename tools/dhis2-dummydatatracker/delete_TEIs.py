
from dhis2 import Api, RequestException, setup_logger, logger, is_valid_uid #make sure you have dhis2.py installed, otherwise run "pip3 install dhis2.py"
import json

credentials_file = './auth.json'
instance = None

try:
    f = open(credentials_file)
except IOError:
    print("Please provide file auth.json with credentials for DHIS2 server")
    exit(1)
else:
    with open(credentials_file, 'r') as json_file:
        credentials = json.load(json_file)
    if instance is not None:
        api = Api(instance, credentials['dhis']['username'], credentials['dhis']['password'])
    else:
        api = Api.from_auth_file(credentials_file)

setup_logger()


def main():

    logger.warning("Server source running DHIS2 version {} revision {}".format(api.version, api.revision))

    import argparse

    my_parser = argparse.ArgumentParser(prog='delete_TEIs',
                                        description='Delete all TEIs created by robot',
                                        epilog="",
                                        formatter_class=argparse.RawDescriptionHelpFormatter)
    my_parser.add_argument('Program_UID', metavar='program_uid', type=str,
                           help='the uid of the program to use')
    my_parser.add_argument('-ou', '--org_unit', action="store", dest="OrgUnit", type=str,
                           help='Rather than deleting from the root of the tree, deletes from a specific orgUnit including descendants'
                                'Eg: --ou=Q7RbNZcHrQ9')

    args = my_parser.parse_args()
    program_uid = args.Program_UID
    if not is_valid_uid(program_uid):
        logger.error('The program uid specified is not a valid DHIS2 uid')
        exit(1)
    else:
        try:
            program = api.get('programs/' + program_uid).json()
        except RequestException as e:
            if e.code == 404:
                logger.error('Program ' + program_uid + ' specified does not exist')
                exit(1)

    if args.OrgUnit is not None:
        if not is_valid_uid(args.OrgUnit):
            logger.error('The orgunit uid specified is not a valid DHIS2 uid')
            exit(1)
        else:
            try:
                api.get('organisationUnits/' + args.OrgUnit).json()
            except RequestException as e:
                if e.code == 404:
                    logger.error('Org Unit ' + args.OrgUnit + ' specified does not exist')
                    exit(1)

    else:
        pass #TODO Obtain root of the OU tree

    params = {
        'ou': args.OrgUnit,
        'ouMode': 'DESCENDANTS',
        'program': program_uid,
        'skipPaging': 'true',
        #'lastUpdatedDuration': '4d',
        #'fields': '*'
        'fields': 'trackedEntityInstance,enrollments'
    }

    data = api.get('trackedEntityInstances', params=params).json()['trackedEntityInstances']

    logger.info("Found " + str(len(data)) + " TEIs")

    user = credentials['dhis']['username']
    for tei in data:
        # #### Uncomment this to filter by user
        if 'enrollments' not in tei:
            import json
            logger.info(json.dumps(tei, indent=4))
        if tei["enrollments"][0]["storedBy"] != user:
            logger.warning("Skipping tei stored by " + tei["enrollments"][0]["storedBy"])
            continue
        # ####
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