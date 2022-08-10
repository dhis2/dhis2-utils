from logzero import logger, logfile
import argparse
import sys
from dhis2 import is_valid_uid

# setup the logger
logfile("./dummyDataTracker.log")

if __name__ == '__main__':
    my_parser = argparse.ArgumentParser(description='Create dummy data flat file in Google Spreadsheets')
    my_parser.add_argument('Program_UID', metavar='program_uid', type=str,
                           help='the uid of the program to use')
    my_parser.add_argument('--with_teis_from_ou', action="store", dest="OrgUnit", type=str)
    my_parser.add_argument('--stage_repeat', action="append", metavar=('stage_uid', 'number_repeats'), nargs=2)
    args = my_parser.parse_args()

    program_uid = args.Program_UID
    if not is_valid_uid(program_uid):
        print('The program uid specified is not valid')
        sys.exit()
    if args.OrgUnit is not None and not is_valid_uid(args.OrgUnit ):
        print('The orgunit uid specified is not valid')
        sys.exit()
    if args.stage_repeat is not None and len(args.stage_repeat) > 0:
        for param in args.stage_repeat:
            if not is_valid_uid(param[0]):
                print('The program stage uid specified ' + param[0] + ' is not valid')
                sys.exit()
            try:
                int(param[1])
            except ValueError:
                print('The repetition value ' + param[1] + ' is not an integer')
                sys.exit()
