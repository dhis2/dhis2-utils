import argparse
import logging
import json
import myutils
import sys


def main():
    any_error = False
    my_parser = argparse.ArgumentParser(description='Metadata package validator')
    my_parser.add_argument('-f', '--file', action="store", dest="input_filename", type=str, help='input filename')
    args = my_parser.parse_args()

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # create file handler which logs even debug messages
    fh = logging.FileHandler('package_metadata_validator.log', encoding="utf-8")
    # create console handler which logs even debug messages
    ch = logging.StreamHandler()
    # create formatter and add it to the handlers
    formatter = logging.Formatter('* %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.info('-------------------------------------Starting validation-------------------------------------')

    try:
        open(args.input_filename)
    except IOError:
        print("Please provide a valid filename")
        exit(-1)
    else:
        with open(args.input_filename, mode='r', encoding="utf-8") as json_file:
            package = json.load(json_file)

    # -------------------------------------

    # Validation for options
    o_mq_2 = {}
    for option in package["options"]:

        # Group options by optionSet (for O-MQ-2)
        optionSet = option["optionSet"]["id"]
        if optionSet in o_mq_2:
            o_mq_2[optionSet].append(option["sortOrder"])
        else:
            o_mq_2[optionSet] = list()
            o_mq_2[optionSet].append(option["sortOrder"])

    # O-MQ-2: Expected sortOrder for options of an optionSet (starts at 1 and ends at the size of the list of options)
    for optionSet_uid, sortOrders in o_mq_2.items():
        sortOrders.sort() # Order array of sortOrders

        size = len(sortOrders)
        if (sortOrders[0] == 1) and (sortOrders[size - 1] == size):
            pass  # Everything is OK
        else:
            optionSet_name = myutils.get_name_by_type_and_uid(package=package,type="optionSets", uid=optionSet_uid)
            message = "O-MQ-2 - The optionSet '" + optionSet_name + "' (" + optionSet_uid + ") has errors in the sortOrder. Current sortOrder: "+", ".join([str(int) for int in sortOrders])
            logging.error(message)
            any_error = True

    logger.info('-------------------------------------Finished validation-------------------------------------')

    if any_error:
        sys.exit(-1)


if __name__ == '__main__':
    main()
