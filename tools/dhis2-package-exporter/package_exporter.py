# todo: check naming convention for option names
import json
import chardet
from dhis2 import Api, RequestException, setup_logger, logger, is_valid_uid
import sys
import pandas as pd
from re import match, findall, compile, search
import argparse
from tools.json import reindex


def get_metadata_element(metadata_type, filter=""):
    params = {"paging": "false",
              "fields": "*"}
    if filter != "":
        params["filter"] = filter
    try:
        # if the filter is too long, i.e. too many ids, we chunk it to avoid causing a 414 or 400 error
        if len(filter) > 1000:
            filter_list = filter.split(':')
            if len(filter_list) == 3:  # Eg id:in:[id1,id2] should have 3 elements
                id_list = filter_list[2].replace('[', '').replace(']', '').split(',')
                metadata_result = list()
                number_elems = len(id_list)
                # The goal is is to extract the uids in the filter into a list again and then
                # chunk that list in pieces of 100 which can be used in the API call to make sure it works now
                # Jenkins seems to have problems when it is set to 100
                chunk_max_size = 75
                for x in range(0, number_elems, chunk_max_size):
                    chunk_ids = id_list[x:(
                        (x + chunk_max_size) if number_elems > (x + chunk_max_size) else number_elems)]
                    metadata_result += get_metadata_element(metadata_type,
                                                            filter_list[0] + ":" + filter_list[1] + ":[" +
                                                            ','.join(chunk_ids) + "]")
                return metadata_result
        else:
            return api_source.get(metadata_type, params=params).json()[metadata_type]
    except RequestException as e:
        logger.error('Server return ' + str(e.code) + ' when getting ' + metadata_type)
        # if e.code == 414 or e.code == 400:
        sys.exit(1)

    return []


def get_metadata_element_with_fields(metadata_type, filter=""):
    # This function should be removed at some point. The whole purpose is to
    # to provide a workaround for when the API call using * does not work
    params = {"paging": "false",
              "fields": "*"}
    if filter != "":
        params["filter"] = filter
    try:
        # First let's get a small sample with paging = true
        params["paging"] = "true"
        sample = api_source.get(metadata_type, params=params).json()[metadata_type]
        if len(sample) > 0:
            # Get all keys and use them as fields
            params["fields"] = ','.join(sample[0].keys())
            params["paging"] = "false"
            return api_source.get(metadata_type, params=params).json()[metadata_type]
        else:
            return []

    except RequestException as e:
        logger.error('Server return ' + str(e.code) + ' when getting ' + metadata_type)
        # if e.code == 414 or e.code == 400:
        sys.exit(1)

    return []


def remove_subset_from_set(metaobject, subset_key):
    """
    Remove all metadata nested under subset_key from meta object

    Args:
      metaobject (list / dict): metadata object to clean
      subset_key (str): the key to find in the metadata which needs to be removed

    Returns:
        metaobject (list / dict) the json object after removing the key
    """
    # If it is not a list, check if subset key in the dictionary and just remove that key
    if not isinstance(metaobject, list):
        if subset_key in metaobject:
            del metaobject[subset_key]
    else:
        for obj in metaobject:
            # Iterate over the list and remove the key from each object if it is there
            if subset_key in obj:
                del obj[subset_key]

    return metaobject


def json_extract(obj, key):
    """
    Recursively fetch values from nested JSON

    Args:
      obj (list / dict): metadata object
      key (str): the key to find in the metadata object

    Returns:
        values (list) the values found for the key in the object
    """
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(v)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    values = extract(obj, arr, key)
    return values


def json_extract_nested_ids(obj, key):
    """
    Recursively fetch ids for a given key in a nested JSON

    Args:
      obj (list / dict): metadata object
      key (str): the key to find in the metadata object

    Returns:
        values (list) the ids found for the key in the object
    """
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                # if the key is in the dictionary
                if k == key:
                    # the key points to a list eg, key is 'dataElements':
                    # "dataElements" : [
                    #    { "id": "UID1", "id": "UID2", ... }
                    # ]
                    if isinstance(v, list):
                        for item in v:
                            arr.append(item["id"]) if item["id"] not in arr else arr
                    # the key points to another dictionary eg, key is 'dataElement':
                    # "dataElement" : { "id": UID }
                    elif isinstance(v, dict):
                        arr.append(v["id"])
                    # if it is not a list or a dict, we simply take the value eg, key is organisationUnit
                    # "organisationUnit" : UID
                    else:
                        arr.append(v)
                # if key is not there but it is still a dict or a list,
                # call the extract function again to keep going down another level
                elif isinstance(v, (dict, list)):
                    extract(v, arr, key)
        # if it is a list, loop each element and call the extract function
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    values = extract(obj, arr, key)
    # Make sure the returned list contains no duplicate UIDs
    return list(dict.fromkeys(values))


def add_key_value_pair_if_missing(json_object, key, value):
    """
    Add a key with a value to a json object

    Args:
      json_object (list / dict): metadata object
      key (str): the key to add
      value (): the value to add to the new key

    Returns:
        json_object after adding the key/value
    """
    # if the object is a list, we add the key/value in every object of the list, if not present
    if isinstance(json_object, list):
        for item in json_object:
            if key not in json_object:
                item[key] = value
    else:
        # if it is just a dictionary, we simply add the key/value
        if key not in json_object:
            json_object[key] = value
    return json_object


def replace_key(json_object, old_key, new_key):
    """
    Replace an old key with a new key in a json object

    Args:
      json_object (list): metadata object list
      old_key (str): the key to find and replace
      new_key (str): the new key to add which will point the value stored at old_key

    Returns:
        json_object after replacing the key
    """
    if isinstance(json_object, list):
        for item in json_object:
            if old_key in item:
                item[new_key] = item.pop(old_key)
    return json_object


def replace_value(json_object, key, new_value):
    """
    Replace a value linked to a key in a json object

    Args:
      json_object (list): metadata object list
      key (str): the key to find and replace value with
      new_value (): the new value to use for the key

    Returns:
        json_object after replacing the value
    """
    if isinstance(json_object, list):
        for item in json_object:
            if key in item:
                item[key] = new_value
    return json_object


def get_dashboard_elements(dashboard):
    """
    Loop through all dashboard items in a dashboard and extract their UIDs

    Args:
      dashboard (dict): whole metadata of a dashboard in DHIS2

    Returns:
        items (dict): a dict with keys corresponding to every type of dashboard item: chart, reportTable, eventReport...
         containing a list of the UIDs for every elements used in the dashboard
    """
    items = {"visualization": [], "chart": [], "reportTable": [], "eventVisualization": [], "eventReport": [], "eventChart": [], "map": []}
    for dashboardItem in dashboard['dashboardItems']:
        if any(version in api_source.version for version in ['2.36', '2.37']):
            items_list = ['visualization', 'eventVisualization', 'eventReport', 'eventChart', 'map']
        else:
            items_list = ['visualization', 'eventVisualization', 'map']
        for dashboard_item in items_list:
            if dashboard_item in dashboardItem:
                items[dashboard_item].append(dashboardItem[dashboard_item]['id'])
    return items


def get_elements_in_data_dimension(analytics_items, analytics_uids):
    """
    Loop through all items in analytics_items and extract UIDs of dataElement, indicator and programIndicator

    Args:
      analytics_items (list): list of maps, visualizations, eventCharts OR eventReports OR eventVisualizations

    Returns:
        updated version of analytics_uids
    """
    for key in ['dataElement', 'indicator', 'programIndicator', 'attribute']:
        analytics_uids[key] = list(dict.fromkeys(analytics_uids[key] + json_extract_nested_ids(analytics_items, key)))

    return analytics_uids


def remove_undesired_children(parent_group_list, children_uid_list, children_label, verbose=False):
    """
    Remove elements in a group

    Args:
      parent_group_list (list): a list of metadata for all groups in the package
      EG: dataElementGroups, programIndicatorGroups..
      children_uid_list (list): list of uids for the children. Any children uid not in the list must be removed
      children_label (str): the key under which the children can be found, eg: dataElements, programIndicators...

    Returns:
        new_parent_group (list): the parent_group_list after removing the non desired children
    """
    new_parent_group = list()
    for parent_group in parent_group_list:
        new_parent = parent_group.copy()
        current_children_uids = json_extract_nested_ids(parent_group, children_label)
        # Get elements in current group which are not part of the children to use
        diff = list(set(current_children_uids).difference(children_uid_list))
        if len(diff) > 0:  # There are elements which should not be there
            if verbose == True:
                logger.warning(parent_group['name'] + ' (' + parent_group['id'] +
                               ') contains elements which do NOT belong to the package :' + str(diff))
                logger.warning('Elements will be removed from the group')
            # Get the required elements
            children_to_keep = list(set(current_children_uids).difference(diff))
            new_parent[children_label] = list()
            for uid in children_to_keep:
                new_parent[children_label].append({"id": uid})
        new_parent_group.append(new_parent)

    return new_parent_group


# DEPRECATED but might be useful
def programIndicatorGroup_belong_to_program(pig, program_uid):
    # Get the uids of programIndicators
    pi_uids = json_extract_nested_ids(pig, 'programIndicators')
    # Get those program indicators
    programIndicators = api_source.get('programIndicators',
                                       params={"fields": "program",
                                               "filter": "id:in:[" + ','.join(pi_uids) + "]"}).json()[
        'programIndicators']
    # Now get the program_uids
    program_uids = json_extract_nested_ids(programIndicators, 'program')
    # If we find more than one program -> This group contains PI from different programs -> Warning
    if len(program_uids) > 1:
        logger.warning("programIndicatorGroup " + pig["id"] +
                       " has programIndicators which belong to multiple programs: " + ','.join(program_uids))

    if program_uid in program_uids:
        return True
    else:
        return False


def get_hardcoded_values_in_fields(metaobj, metadata_type, fields):
    """
    Find UID of DEs, TEAs, constants used in a string. DE: #{ProgramStageUID.UID}, TEA: A{UID}, Constant: C{UID}

    Args:
      metaobj (list or just one element of a list): metadata to scan
      metadata_type (str): supports dataElements, trackedEntityAttributes and constants
      fields (list): a list of strings representing the fields to scan in the metadata,
      eg: condition, filter, expression..
    Returns:
        result (list): a list of unique UIDs found
    """
    result = list()
    if not isinstance(fields, list):
        fields = [fields]
    # For predictors we need to go down another level, since it is generator.expression
    second_level = ""
    for field in fields:
        if '.' in field:
            tmp = field.split('.')
            fields[fields.index(field)] = tmp[0]
            second_level = tmp[1]

    if isinstance(metaobj, list):
        for element in metaobj:
            for key in element:
                if key in fields:
                    if metadata_type == 'dataElements_ind' or metadata_type == 'categoryOptionCombos':
                        pattern = compile(r'#\{([a-zA-Z0-9]{11})\.*([a-zA-Z0-9]{11})*\}')
                    elif metadata_type == 'dataElements_prgInd':
                        pattern = compile(r'#\{[a-zA-Z0-9]{11}\.([a-zA-Z0-9]{11})\}')
                    elif metadata_type == 'programIndicators':
                        pattern = compile(r'I\{([a-zA-Z0-9]{11})\}')
                    elif metadata_type == 'trackedEntityAttributes':
                        pattern = compile(r'A\{([a-zA-Z0-9]{11})\}')
                    elif metadata_type == 'constants':
                        pattern = compile(r'C\{([a-zA-Z0-9]{11})\}')
                    elif metadata_type == 'organisationUnitGroups':
                        pattern = compile(r'OUG\{([a-zA-Z0-9]{11})\}')
                    else:
                        logger.error('Error in function get_hardcoded_values_in_fields: unknown type ' + metadata_type)
                    if second_level != "":
                        z = pattern.findall(element[key][second_level])
                    else:
                        z = pattern.findall(element[key])
                    if z:
                        for z_match in z:
                            # For the case of a DE + COC, we will capture a tuple. In that case we only keep the first
                            # which is the DE
                            if isinstance(z_match, tuple):
                                if metadata_type == 'dataElements_ind':
                                    uid = z_match[0]
                                elif metadata_type == 'categoryOptionCombos':
                                    uid = z_match[1]
                            else:
                                uid = z_match
                            if is_valid_uid(uid):
                                result.append(uid)
    return result


def update_last_updated(metaobj, metadata_type):
    """
    Updates dataframe df_report_lastUpdated containing lastUpdated and lastUpdatedBy info for every element
    in the package

    Args:
      metaobj (list): metadata to process
      metadata_type (str): metadata type we are processing. Needed to categorize the elements on the table
    Returns:
        None
    """
    global df_report_lastUpdated
    global users
    if isinstance(metaobj, list):
        for item in metaobj:
            if 'lastUpdated' in item:
                last_updated = item['lastUpdated']
            else:
                last_updated = 'NOT AVAILABLE'
            id = item['id']
            if 'name' in item:
                name = item['name']
            elif 'displayName' in item:
                name = item['displayName']
            else:
                name = ""
            if 'code' in item:
                code = item['code']
            else:
                code = ""
            # datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')
            if 'lastUpdatedBy' in item and 'name' in item['lastUpdatedBy']:
                last_updated_by = item['lastUpdatedBy']['name']
            else:
                last_updated_by = 'NOT AVAILABLE'
            # Add to dataframe
            df_report_lastUpdated = df_report_lastUpdated.append(
                {'metadata_type': metadata_type, 'uid': id, 'name': name, 'code': code,
                 'last_updated': last_updated, 'updated_by': last_updated_by}
                , ignore_index=True)


def clean_metadata(metaobj):
    """
    Remove undesired keys from metadata

    Args:
      metaobj (list): metadata to process
    Returns:
        metaobj (list): same metadata after cleaning
    """
    if len(metaobj) == 1 and 'href' in metaobj[0] and '/api/programs/' in metaobj[0]['href']:
        metaobj = metaobj  # Keep lastUpdated for program
    else:
        metaobj = remove_subset_from_set(metaobj, 'lastUpdated')
    metaobj = remove_subset_from_set(metaobj, 'lastUpdatedBy')
    metaobj = remove_subset_from_set(metaobj, 'created')
    metaobj = remove_subset_from_set(metaobj, 'createdBy')
    metaobj = remove_subset_from_set(metaobj, 'href')
    metaobj = remove_subset_from_set(metaobj, 'access')
    metaobj = remove_subset_from_set(metaobj, 'favorites')
    metaobj = remove_subset_from_set(metaobj, 'allItems')
    metaobj = remove_subset_from_set(metaobj, 'displayName')
    metaobj = remove_subset_from_set(metaobj, 'displayFormName')
    metaobj = remove_subset_from_set(metaobj, 'displayShortName')
    metaobj = remove_subset_from_set(metaobj, 'displayDenominatorDescription')
    metaobj = remove_subset_from_set(metaobj, 'displayNumeratorDescription')
    metaobj = remove_subset_from_set(metaobj, 'displayDescription')
    metaobj = remove_subset_from_set(metaobj, 'interpretations')
    if len(metaobj) > 0:
        for subtag in ['dashboardItems', 'analyticsPeriodBoundaries', 'mapViews', 'user', 'userGroupAccesses',
                       'programStageDataElements', 'programTrackedEntityAttributes',
                       'trackedEntityTypeAttributes', 'userCredentials', 'legends', 'greyedFields']:
            for i in range(0, len(metaobj)):
                if subtag in metaobj[i]:
                    metaobj[i][subtag] = remove_subset_from_set(metaobj[i][subtag], 'lastUpdated')
                    metaobj[i][subtag] = remove_subset_from_set(metaobj[i][subtag], 'lastUpdatedBy')
                    metaobj[i][subtag] = remove_subset_from_set(metaobj[i][subtag], 'created')
                    metaobj[i][subtag] = remove_subset_from_set(metaobj[i][subtag], 'createdBy')
                    # There is access : { read: true, delete: false ... } dictionary
                    # and there is access : "rw----"... Make sure we only delete the dictionary version
                    if subtag not in ['user', 'userGroupAccesses']:
                        metaobj[i][subtag] = remove_subset_from_set(metaobj[i][subtag], 'access')

                    if subtag == 'programTrackedEntityAttributes':
                        metaobj[i][subtag] = remove_subset_from_set(metaobj[i][subtag], 'name')
                    metaobj[i][subtag] = remove_subset_from_set(metaobj[i][subtag], 'displayName')
                    metaobj[i][subtag] = remove_subset_from_set(metaobj[i][subtag], 'displayFormName')
                    metaobj[i][subtag] = remove_subset_from_set(metaobj[i][subtag], 'displayShortName')

    return metaobj


def check_sharing(json_object, omit=[], verbose=False):
    """
    Check publicAccess, user, users, userAccesses and userGroupAccesses for particular list of metadata objects
    It also performs some corrections (for example, adding package_admin user, removing some undesired User Groups in sharing..)
    Args:
      json_object (list): metadata to process
      omit (list): can be used to omit certain keys
      verbose (bool): if True, it gives warnings to the users. It is set to False because it was adding too many
      messages in the screen
    Returns:
        metaobj (list): same metadata after cleaning
    """
    if isinstance(json_object, list):
        for item in json_object:
            # Check public access
            if 'publicAccess' in item and 'publicAccess' not in omit:
                if item['publicAccess'][1:2] == 'w':
                    if verbose:
                        logger.warning(
                            'Element ' + item["id"] + ' has write public access ' + item['publicAccess'][0:2])
            if 'user' in item and 'user' not in omit:
                if item['user']['id'] != package_admin_uid:
                    if verbose:
                        logger.warning('Element ' + item["id"] + ' has wrong user: ' + item['user'][
                            'id'] + '... Replacing with package_admin')
                    user_package_admin = {'id': package_admin_uid, 'name': 'package admin', 'username': 'package_admin'}
                    for key in list(item['user']):
                        if key not in user_package_admin:
                            del item['user'][key]
                        else:
                            item['user'][key] = user_package_admin[key]
            if 'users' in item and isinstance(item['users'], list) and 'users' not in omit:
                users = item['users']
                outsiders = list()
                for user in users:
                    if user['id'] != package_admin_uid:
                        outsiders.append(user["id"])
                if len(outsiders) > 0:
                    if verbose:
                        logger.warning('Element ' + item["id"] + ' is shared with wrong users : ' + str(
                            outsiders) + '... Correcting')
                    item['users'] = []
            if 'userAccesses' in item and len(item['userAccesses']) > 0:
                if verbose:
                    logger.warning('Element ' + item["id"] + ' is shared with specific users... Removing')
                item['userAccesses'] = []
            if 'userGroupAccesses' in item and 'userGroupAccesses' not in omit:
                correct_user_groups = list()
                outsider_user_groups = list()
                for uga in item['userGroupAccesses']:
                    if uga['id'] not in userGroups_uids:
                        message = ""
                        message += uga['id']
                        if 'name' in uga:
                            message += ' - ' + uga['name']
                        outsider_user_groups.append(message)
                    else:
                        correct_user_groups.append(uga)
                item['userGroupAccesses'] = correct_user_groups
                if len(outsider_user_groups) > 0:
                    if verbose:
                        logger.warning(
                            'Element ' + item["id"] + ' is shared with a User Group(s) outside the package: ' +
                            ', '.join(outsider_user_groups) + '... Deleted')
            # Starting in 2.36 a new sharing object was introduced
            if 'sharing' in item and 'sharing' not in omit:
                if 'owner' in item['sharing']:
                    item['sharing']['owner'] = package_admin_uid
                # Clean users, we share always with userGroups
                item['sharing']['users'] = {}
                # Process userGroups in sharing
                userGroupIds = list(item['sharing']['userGroups'].keys())
                for userGroupId in userGroupIds:
                    if userGroupId not in userGroups_uids:
                        item['sharing']['userGroups'].pop(userGroupId, None)

    return json_object


def check_and_replace_root_ou_assigned(metaobj):
    """
    In some cases, certain visualizations need to have the OU Root in the metadata
    This functions check that for those specific cases, the OU UID is replaced by a placeholder
    It also warns the user

    Args:
      metaobj (list): metadata to process

    Returns:
        metaobj (list): same metadata after cleaning
    """
    if isinstance(metaobj, list):
        root_uid = ""
        placeholder = '<OU_ROOT_UID>'
        for obj in metaobj:
            root_uid_replaced = False
            if 'organisationUnits' in obj and len(obj['organisationUnits']) == 1 and \
                    'userOrganisationUnit' in obj and obj['userOrganisationUnit'] == False and \
                    'userOrganisationUnitChildren' in obj and obj['userOrganisationUnitChildren'] == False and \
                    'userOrganisationUnitGrandChildren' in obj and obj['userOrganisationUnitGrandChildren'] == False:
                if root_uid == "":
                    # Get the root UID
                    root_ou = get_metadata_element('organisationUnits', 'level:eq:1')
                    if len(root_ou) > 1:
                        logger.warning('More than one OU root found in OU Tree')
                    root_uid = root_ou[0]['id']
                if obj['organisationUnits'][0]['id'] == root_uid:
                    # Remove and use a placeholder
                    obj['organisationUnits'][0] = {'id': placeholder}
                    root_uid_replaced = True
            elif len(obj['organisationUnits']) > 1:
                # In this case we have a list of organisation units. Remove them and raise a warning
                obj['organisationUnits'] = []
                logger.warning(
                    "The dashboard item with UID " + obj['id'] + " has organisation units assigned... Removing")
            # Remove and use a placeholder also for parentGraphMap
            if 'parentGraphMap' in obj and obj['parentGraphMap'] and root_uid in obj['parentGraphMap']:
                obj['parentGraphMap'][placeholder] = obj['parentGraphMap'][root_uid]
                del obj['parentGraphMap'][root_uid]
                root_uid_replaced = True

            if root_uid_replaced:
                # Warn the user
                logger.warning('Element ' + obj['id'] + ' has root OU assigned to it ('
                               + root_uid + ')... Replacing with placeholder: ' + placeholder)

    return metaobj


def replace_organisation_level_with_placeholder(metaobj):
    """
    Find organisationUnitLevels key and replaces the UID with a placeholder

    Args:
      metaobj (list): metadata to process

    Returns:
        metaobj (list): same metadata after replacing placeholder
    """

    # get organisationUnitLevels
    org_unit_levels = get_metadata_element('organisationUnitLevels')
    placeholder_dict = dict()
    for level in org_unit_levels:
        placeholder_dict[level['id']] = '<OU_LEVEL_' + level['name'].upper() + '_UID>'
    # We expect a list of elements
    if isinstance(metaobj, list):
        for element in metaobj:
            if 'organisationUnitLevels' in element:
                for index in range(0, len(element['organisationUnitLevels'])):
                    element['organisationUnitLevels'][index]['id'] = \
                        placeholder_dict[element['organisationUnitLevels'][index]['id']]

    return metaobj


# def check_naming_convention(metaobj, health_area, package_prefix):
#     """
#     Check if name is in te standard format "PREFIX - "
#
#     Args:
#       metaobj (list): metadata to process
#       package_prefix (str) - intervention, e.g. CS, EIR, etc...
#
#     Returns:
#         metaobj (list): same metadata after removing potential undesired matches
#     """
#     filtered_list = list()
#     # Try new naming convention health area + prefix, e.g. MAL-CS-
#     for element in metaobj:
#         # Remove leading and trailing spaces and any extra white spaces
#         name = element['code'].strip()
#         # Prefix should come at the beginning
#         # if (element['name'].find(package_prefix)) == 0:
#         if search(pattern="^" + package_prefix + "[.]?[0-9]{0,2}[ ]?[-]?[ ]?", string=name):
#             filtered_list.append(element)
#     # if len(filtered_list) == 0:
#     #     # Try old naming convention ONLY prefix - TO BE REMOVED
#     #     for element in metaobj:
#     #         # Handle special case where the name equals the package prefix
#     #         if element['code'] == package_prefix:
#     #             filtered_list.append(element)
#     #             continue
#     #         if (element['code'].find(package_prefix)) == 0:
#     #             if search(pattern="^" + package_prefix + "[.]?[0-9]{0,2}[ ]?[-]?[ ]?", string=name):
#     #                 filtered_list.append(element)
#     if len(filtered_list) == 0:
#         # Try just health area elements
#         for element in metaobj:
#             name = element['code']
#             if search(pattern="^" + health_area + "[.]?[0-9]{0,2}[ ]?[-]?[ ]?", string=name):
#                 filtered_list.append(element)
#     if len(filtered_list) == 0:
#         # Last chance
#         for element in metaobj:
#             name = element['code'].strip()
#             name = ' '.join(name.split())
#             # Try again and consider other options
#             if search(pattern="^[ ]*" + package_prefix + "[ ]?[_:]?[ ]?", string=name):
#                 filtered_list.append(element)
#                 logger.warning('Adding element with wrong naming convention to package: ' + name)
#             elif search(pattern="^[0-9]{0,2}[.]?[ ]*" + package_prefix + "[ ]?[_:]?[ ]?", string=name):
#                 filtered_list.append(element)
#                 logger.warning('Adding element with wrong naming convention to package: ' + name)
#     return filtered_list


def check_issues_with_program_rules(metaobj, elem_list, elem_type='DE'):
    """
    Check broken references in program rules "

    Args:
      metaobj (dict): contains programRules, programRuleActions, programRuleVaribles,
      dataElements, trackedEntityAttributes
      elem_list (list): uids of DE or TEAs to analyze
      elem_type (str): DE or TEA

    Returns:
        metaobj (list): same metadata after removing potential undesired matches
    """

    if elem_type == "DE":
        type = 'dataElement'
    else:
        type = 'trackedEntityAttribute'

    # Get the elements to improve the verbose
    DEs = get_metadata_element(type + "s", "id:in:[" + ','.join(elem_list) + "]")

    for UID in elem_list:
        # Find the name
        found = False
        for elem in DEs:
            if elem['id'] == UID:
                logger.info(type + " with " + UID + " : " + elem['name'])
                found = True
                break
        if found:
            found_prv = False
            found_pra = False
            prv_list = list()
            pra_list = list()
            pr_list = list()
            prv_index = -1
            for prv in metaobj['programRuleVariables']:
                prv_index += 1
                if type in prv and prv[type]['id'] == UID:
                    logger.info("   Used in programRuleVariable with " + prv['id'] + " : " + prv['name'])
                    # SOFT DELETE in package ########################
                    del metaobj['programRuleVariables'][prv_index]
                    # HARD DELETE in instance #######################
                    # api_source.delete('programRuleVariables/' + prv['id'])
                    found_prv = True
                    prv_list.append(prv['name'])
            pra_index = -1
            for pra in metaobj['programRuleActions']:
                pra_index += 1
                if type in pra and pra[type]['id'] == UID:
                    logger.info("   Used in programRuleAction with " + pra['id'])
                    # SOFT DELETE in package ########################
                    del metaobj['programRuleActions'][pra_index]
                    # HARD DELETE in instance #######################
                    # pr_object = api_source.get('programRules/' + pra['programRule']['id']).json()
                    # pra_list_after_removing = list()
                    # for current_pra in pr_object['programRuleActions']:
                    #     if pra['id'] != current_pra["id"]:
                    #         pra_list_after_removing.append(current_pra)
                    # pr_object['programRuleActions'] = pra_list_after_removing
                    # try:
                    #     response = api_source.put('programRules/' + pra['programRule']['id'],
                    #                    params={'mergeMode': 'REPLACE', 'importStrategy': 'CREATE_AND_UPDATE'},
                    #                    json=pr_object)
                    # except RequestException as e:
                    #     logger.error("metadata update failed with error " + str(e))
                    #     sys.exit()
                    # # NOT NEEDED if above statement works  - api_source.delete('programRuleActions/' + pra['id'])
                    found_pra = True
                    pra_list.append(pra['id'])
                    pr_list.append(pra['programRule']['id'])
            if found_prv or found_pra:
                found_pr = False
                pr_index = -1
                for pr in metaobj['programRules']:
                    pr_index += 1
                    if found_prv:
                        for prv_name in prv_list:
                            # look for it in the condition:
                            pattern = compile(r'\{(' + prv_name + ')\}')
                            z = pattern.findall(pr['condition'])
                            # Could this be also used in PRA data?
                            if z:
                                logger.info("   Used in programRule with " + pr['id'] + " : " + pr['name'])
                                # SOFT DELETE in instance #######################
                                logger.warning("   Consider DELETING the PR from the package")
                                # HARD DELETE in instance #######################
                                # api_source.delete('programRules/' + pr['id'])
                                found_pr = True
                    if found_pra:
                        for pr_uid in pr_list:
                            if pr['id'] == pr_uid:
                                logger.info("   Used in programRule with " + pr['id'] + " : " + pr['name'])
                                # SOFT DELETE in instance #######################
                                # We will delete the PR if all PRA have been also deleted
                                delete = True
                                for pra_in_pr in pr['programRuleActions']:
                                    if pra_in_pr['id'] not in pra_list:
                                        delete = False
                                        break
                                if delete:
                                    del metaobj['programRules'][pr_index]
                                # HARD DELETE in instance #######################
                                # api_source.delete('programRules/' + pr['id'])
                                found_pr = True
                if not found_pr:
                    logger.warning("   NOT Used in ANY programRule")


def get_category_elements(cat_combo_uid, cat_uid_dict=None):
    """
    Get all elements referenced by a cat combo

    Args:
      cat_combo_uid (str): uid of the category combonation

    Returns:
        cat (dict): dictionary with results
    """
    # @todo

    if cat_uid_dict is None:
        cat = dict()
        cat['categoryOptions'] = list()
        cat['categories'] = list()
        cat['categoryCombos'] = list()
        cat['categoryOptionCombos'] = list()
        cat['categoryOptionGroups'] = list()
        cat['categoryOptionGroupSets'] = list()
        cat['categoryOptionsFromCOCs'] = list()
    else:
        cat = cat_uid_dict

    # Get categoryCombos info, which will give us categoryOptionCombos and categories
    catCombo = api_source.get('categoryCombos/' + cat_combo_uid,
                              params={"fields": "id,name,code,categories,categoryOptionCombos"}).json()
    if 'code' not in catCombo or catCombo['code'].lower() != 'default':
        cat['categoryCombos'] = list(dict.fromkeys(cat['categoryCombos'] + [cat_combo_uid]))
        cat['categories'] = list(dict.fromkeys(cat['categories'] + json_extract_nested_ids(catCombo, 'categories')))
        # Get the categoryOptions of that category
        COs = api_source.get('categoryOptions', params={"fields": "id,name", "paging": "false",
                                                              "filter": "categories.id:in:[" + ','.join(
                                                                  cat['categories']) + "]"}).json()[
            'categoryOptions']
        cat['categoryOptions'] = list(dict.fromkeys(cat['categoryOptions'] + json_extract(COs, 'id')))
        # Get the categoryOptionCombos generated by that CC
        COCs = api_source.get('categoryOptionCombos', params={"fields": "id,name,categoryCombo,categoryOptions", "paging": "false",
                                                              "filter": "categoryCombo.id:in:[" + cat_combo_uid + "]"}).json()[
            'categoryOptionCombos']
        cat['categoryOptionCombos'] = list(
            dict.fromkeys(cat['categoryOptionCombos'] + json_extract(COCs, 'id')))

        for coc in COCs:
            cat['categoryOptionsFromCOCs'] = list(
                dict.fromkeys(cat['categoryOptionsFromCOCs'] + json_extract_nested_ids(coc, 'categoryOptions')))

    return cat


def add_category_option_combo(cat_opt_combo_uid, cat_uid_dict=None):
    cat_combo_uid = api_source.get('categoryOptionCombos/' + cat_opt_combo_uid,
                                   params={"fields": "id,categoryCombo"}).json()['categoryCombo']['id']
    get_category_elements(cat_combo_uid, cat_uid_dict)


# Not needed for now
def add_metadata_object_list_with_merge(current_metadata_obj, new_metadata_obj, metadata_type):
    # Get current UIDs
    current_metadata_uids = json_extract(current_metadata_obj, 'id')
    for metadata_element in new_metadata_obj:
        if metadata_element['id'] not in current_metadata_uids:
            current_metadata_obj.append(metadata_element)
        else:
            # Merge groups:
            # The idea is that we might have the same DEG in two different packages, but rather than adding it twice
            # or keeping the current one, we can try to merge the UIDs
            # Find the element with same id
            index_of_element = 0
            for current_metadata_element in current_metadata_obj:
                if current_metadata_element['id'] == metadata_element['id']:
                    # Need to look at Sets
                    if metadata_type in ['dataElements', 'options', 'indicators', 'categoryOptions',
                                         'programIndicators', 'predictors', 'validationRules']:
                        key = metadata_type[:-1] + 'Groups'
                    elif metadata_type in ['dataElementGroups', 'optionGroups', 'indicatorGroups',
                                           'categoryOptionGroups', 'programIndicatorGroups', 'predictorGroups',
                                           'validationRuleGroups']:
                        key = metadata_type.replace('Groups', '') + 's'
                    else:
                        key = None
                    if key is not None and key in metadata_element and key in current_metadata_element and \
                            len(metadata_element[key]) > 0 and len(current_metadata_element[key]) > 0:
                        logger.warning('MERGING A GROUP')
                        # Get ids from both of them
                        current_uids = json_extract(current_metadata_element[key], 'id')
                        new_uids = json_extract(metadata_element[key], 'id')
                        all_unique_uids = list(set(current_uids) | set(new_uids))
                        current_metadata_obj[index_of_element][key] = list()
                        for uid in all_unique_uids:
                            current_metadata_obj[index_of_element][key].append({'id': uid})

                index_of_element += 1

    return current_metadata_obj


def main():
    global api_source
    global userGroups_uids
    global df_report_lastUpdated
    global package_admin_uid
    global users

    my_parser = argparse.ArgumentParser(description='Export package')
    my_parser.add_argument('package_type_or_uid', metavar='package_type_or_uid', type=str,
                           help='package type from [TRK,EVT,AGG,DSH,GEN] or UID(s) separated with commas')
    my_parser.add_argument('package_prefix', metavar='package_prefix', type=str,
                           help='the package prefix to look for in the metadata code')
    my_parser.add_argument('package_code', metavar='package_code', type=str,
                           help='the code corresponding to the package')
    my_parser.add_argument('-i', '--instance', action="store", dest="instance", type=str,
                           help='instance to extract the package from (robot account is required!) - tracker_dev by default')
    my_parser.add_argument('-desc', '--description', action="store", dest="description", type=str,
                           help='Description of the package or any comments you want to add')
    my_parser.add_argument('-vb', '--verbose', dest='verbose', action='store_true')
    my_parser.set_defaults(verbose=False)
    my_parser.add_argument('-od', '--only_dashboards', dest='only_dashboards', action='store_true')
    my_parser.set_defaults(only_dashboards=False)

    args = my_parser.parse_args()

    # Prepare the log
    log_file = "./package_export.log"
    import os

    if os.path.exists(log_file):
        try:
            os.remove(log_file)
        except PermissionError:
            pass
    setup_logger(log_file)
    pd.set_option("display.max_rows", None, "display.max_columns", None, "max_colwidth", 1000)
    df_report_lastUpdated = pd.DataFrame({},
                                         columns=['metadata_type', 'uid', 'name', 'code', 'last_updated', 'updated_by'])
    total_errors = 0

    # We need to connect to instance to be able to validate the parameters

    credentials_file = 'auth.json'

    try:
        f = open(credentials_file)
    except IOError:
        print("Please provide file auth.json with credentials for DHIS2 server")
        exit(1)
    else:
        with open(credentials_file, 'r') as json_file:
            credentials = json.load(json_file)
        if args.instance is not None:
            api_source = Api(args.instance, credentials['dhis']['username'], credentials['dhis']['password'])
        else:
            api_source = Api.from_auth_file(credentials_file)

    print("Server source for package extraction {}".format(api_source.base_url))
    print("Running DHIS2 version {} revision {}".format(api_source.version, api_source.revision))
    print("Username: {}".format(credentials['dhis']['username']))
    users = reindex(get_metadata_element('users'), 'id')

    package_type_or_uid = args.package_type_or_uid
    package_prefix = args.package_prefix
    package_code = args.package_code

    # Process now the prefix. We accept multiple prefixes
    all_package_prefixes = package_prefix.split(',')

    program_uids = list()
    programs = None
    dataset_uids = list()
    dataSets = None
    dashboard_uids = list()
    dashboards = None
    if package_type_or_uid not in ['AGG', 'TRK', 'EVT', 'DSH', 'GEN']:
        uids = package_type_or_uid.split(',')
        for uid in uids:
            if not is_valid_uid(uid):
                logger.error('The UID ' + uid + ' is NOT valid')
                exit(1)
        # Check if they are uids of programs
        try:
            programs = api_source.get('programs',
                                      params={"paging": "false",
                                              "fields": "id,name,enrollmentDateLabel,programTrackedEntityAttributes,programStages,programRuleVariables,organisationUnits,trackedEntityType,version,categoryCombo",
                                              "filter": "id:in:[" + package_type_or_uid + "]"}).json()['programs']
        except RequestException as e:
            # if e.code == 404:
            #     logger.warning('Program ' + package_type_or_uid + ' does not exist')
            #     sys.exit()
            pass
        else:
            for program in programs:
                program_uids.append(program['id'])
            if len(programs) == len(uids):
                is_tracker = False
                is_event = False
                for program in programs:
                    if 'trackedEntityType' in program:
                        is_tracker = True
                    else:
                        is_event = True
                if is_tracker and is_event:
                    logger.error("NOT supported: The UIDs provided mix tracker and event programs")
                    exit(1)
                elif is_tracker:
                    package_type_or_uid = 'TRK'
                elif is_event:
                    package_type_or_uid = 'EVT'
            elif len(programs) > 0:
                for program in programs:
                    program_uids.append(program['id'])
                logger.error("Some program UIDs could not be found: " + str(set(uids).difference(program_uids)))
                exit(1)

        # If we could not find the uids as programs, let's try dataSets
        if package_type_or_uid not in ['TRK', 'EVT']:
            # Check if it is a dataSet
            try:
                dataSets = api_source.get('dataSets',
                                          params={"paging": "false",
                                                  "fields": "*",
                                                  "filter": "id:in:[" + package_type_or_uid + "]"}).json()['dataSets']
            except RequestException as e:
                # if e.code == 404:
                #     logger.warning('dataSet ' + package_type_or_uid + ' does not exist')
                #     sys.exit()
                pass
            else:
                for dataSet in dataSets:
                    dataset_uids.append(dataSet['id'])
                if len(dataSets) == len(uids):
                    package_type_or_uid = 'AGG'
                elif len(dataSets) > 0:
                    logger.error("Some dataSet UIDs could not be found: " + str(set(uids).difference(dataset_uids)))
                    exit(1)
    else:
        # Let's get all the elements by code in this case
        # Aggregate package - dataSets
        if package_type_or_uid == 'AGG':
            dataSets = list()
            try:
                for prefix in all_package_prefixes:
                    dataSets += api_source.get('dataSets',
                                               params={"paging": "false",
                                                       "filter": "code:$like:" + prefix,
                                                       "fields": "*"}).json()['dataSets']

            except RequestException as e:
                pass
            else:
                for ds in dataSets:
                    dataset_uids.append(ds['id'])
        # Tracker or event - program
        elif package_type_or_uid in ['TRK', 'EVT']:
            tmp_programs = list()
            try:
                for prefix in all_package_prefixes:
                    tmp_programs += api_source.get('programs',
                                                   params={"paging": "false",
                                                           "filter": "code:$like:" + prefix,
                                                           "fields": "*"}).json()['programs']
                programs = list()
                for program in tmp_programs:
                    # A tracker program has a 'trackedEntityType'
                    if package_type_or_uid == 'TRK' and 'trackedEntityType' in program:
                        programs.append(program)
                    elif package_type_or_uid == 'EVT' and 'trackedEntityType' not in program:
                        programs.append(program)
            except RequestException as e:
                pass
            else:
                for program in programs:
                    program_uids.append(program['id'])

        # Get the dashboards by code
        elif package_type_or_uid == 'DSH':
            dashboards = list()
            try:
                for prefix in all_package_prefixes:
                    dashboards += api_source.get('dashboards',
                                                 params={"paging": "false",
                                                         "filter": "code:$like:" + prefix,
                                                         "fields": "*"}).json()['dashboards']
            except RequestException as e:
                pass
            else:
                for dsh in dashboards:
                    dashboard_uids.append(dsh['id'])

    if args.only_dashboards:
        message_only_dashboard = "DASHBOARD for "
    else:
        message_only_dashboard = ""

    if programs is not None and len(programs) > 0 and len(program_uids) > 0:
        logger.info(
            'Exporting ' + message_only_dashboard + package_type_or_uid + ' program(s) ' + ','.join(program_uids))
    elif dataSets is not None and len(dataSets) > 0 and len(dataset_uids) > 0:
        logger.info('Exporting ' + message_only_dashboard + 'AGG dataSet(s) ' + ','.join(dataset_uids))
    elif dashboards is not None and len(dashboards) > 0 and len(dashboard_uids) > 0:
        logger.info('Exporting ' + message_only_dashboard + 'DSH dashboard(s) ' + ','.join(dashboard_uids))
    elif package_type_or_uid == 'GEN':
        logger.info('Exporting GEN package:  ' + package_prefix)
    else:
        logger.error('The parameters (' + args.package_type_or_uid + ', ' + args.package_prefix + ', ' +
                     args.package_code + ') returned no result for programs / dataSets / dashboards')
        exit(1)

    if package_type_or_uid in ['TRK', 'EVT']:
        # Iteration over this list happens in reversed order
        # Altering the order can cause the script to stop working
        metadata_import_order = [
            'categoryOptionGroupSets', 'categoryOptionGroups',
            'categoryOptions', 'categories', 'categoryOptionCombos', 'categoryCombos',
            'legendSets',  # used in indicators, optionGroups, programIndicators and trackedEntityAttributes
            'optionGroups', 'options', 'optionSets',
            'sqlViews', 'reports', 'constants', 'documents', 'attributes',
            'dataEntryForms', 'sections', 'dataSets',  # Some programs, like HIV, have dataSets
            'dataElements', 'dataElementGroups',
            'validationNotificationTemplates', 'validationRules', 'validationRuleGroups',
            'jobConfigurations',
            'predictors', 'predictorGroups',
            'trackedEntityAttributes', 'trackedEntityTypes', 'trackedEntityInstanceFilters',
            'programNotificationTemplates',
            'programs', 'programSections',
            'programStageSections', 'programStages',
            'programIndicatorGroups', 'programIndicators',
            'organisationUnitGroupSets', 'organisationUnitGroups',  # Assuming this will only be found in indicators
            'indicatorTypes', 'indicatorGroupSets', 'indicators', 'indicatorGroups',
            'programRuleVariables', 'programRuleActions', 'programRules',
            'visualizations', 'maps', 'eventVisualizations', 'eventReports', 'eventCharts', 'dashboards',
            'package', 'users', 'userGroups']
        if package_type_or_uid == 'EVT':
            metadata_import_order.remove('trackedEntityAttributes')
            metadata_import_order.remove('trackedEntityTypes')
            metadata_import_order.remove('trackedEntityInstanceFilters')

    elif package_type_or_uid == 'DSH' or args.only_dashboards:
        metadata_import_order = [
            'categoryOptionGroupSets', 'categoryOptionGroups',
            'legendSets',
            'indicatorTypes', 'indicatorGroupSets', 'indicators', 'indicatorGroups',
            'visualizations', 'maps', 'eventVisualizations', 'eventReports', 'eventCharts', 'dashboards',
            'package', 'users', 'userGroups']

    # Dataset
    elif package_type_or_uid == 'AGG':
        # This list is looped backwards
        metadata_import_order = [
            'categoryOptionGroupSets', 'categoryOptionGroups',
            'categoryOptions', 'categories', 'categoryOptionCombos', 'categoryCombos',
            'legendSets',  # used in indicators, optionGroups, programIndicators and trackedEntityAttributes
            'optionGroups', 'options', 'optionSets',
            'sqlViews', 'reports', 'constants', 'documents', 'attributes',
            'dataEntryForms',
            'dataElements', 'dataElementGroups',  # group first
            'validationNotificationTemplates', 'validationRules', 'validationRuleGroups',  # group first
            'jobConfigurations',
            'predictors', 'predictorGroups',  # group first
            'organisationUnitGroupSets', 'organisationUnitGroups',  # Assuming this will only be found in indicators
            'indicatorTypes', 'indicatorGroupSets', 'indicators', 'indicatorGroups',
            # groups first, to get indicator uids
            'sections', 'dataSets',
            'visualizations', 'maps', 'eventVisualizations', 'eventReports', 'eventCharts', 'dashboards',
            'package', 'users', 'userGroups']

    elif package_type_or_uid == 'GEN':
        metadata_import_order = [
            'categoryOptions', 'categoryOptionGroups',  # 'categoryCombos',
            'options', 'optionSets',
            'dataElements', 'dataElementGroups',
            'indicatorTypes', 'indicators', 'indicatorGroups',
            'trackedEntityAttributes', 'trackedEntityTypes',
            'package']

    # Starting from >=2.38, eventReports and eventCharts are called eventVisualizations
    if any(version in api_source.version for version in ['2.36', '2.37']):
        if 'eventVisualizations' in metadata_import_order:
            metadata_import_order.remove('eventVisualizations')
    else:
        if 'eventReports' in metadata_import_order and 'eventCharts' in metadata_import_order:
            metadata_import_order.remove('eventReports')
            metadata_import_order.remove('eventCharts')

    metadata = dict()

    # todo: these could be part of a big dictionary instead of having individual keys
    userGroups_uids = list()
    dashboard_items = {"visualization": [], "eventReport": [], "eventChart": [],
                       "eventVisualization": [], "map": []}
    attributes_uids = ['iehcXLBKVWM',  # Code (ICD-10)
                       'mpXON5igCG1',  # Code (Loinc)
                       'I6u65yRc0ct',  # Code SNOMED
                       'vudyDP7jUy5']  # Data element for aggregate data export
    dataDimension_uids = {'dataElement': [], 'indicator': [], 'programIndicator': [], 'attribute': []}
    dataSetElements_uids = {'indicator': []}
    dataEntryForms_uids = list()
    dataElements_in_package = list()
    dataElements_uids = dict()
    dataElements_uids['PR'] = list()
    dataElements_uids['PS'] = list()
    dataElements_uids['PSS'] = list()
    dataElements_uids['DEG'] = list()
    dataElements_uids['PI'] = list()
    dataElements_uids['PRED'] = list()
    dataElements_uids['DS'] = list()
    dataElements_uids['VR'] = list()
    dataElements_with_program_prefix_uids = list()
    dataElementsGroups_uids = list()
    categoryOptionCombos_uids = list()
    indicator_uids = list()
    predictor_uids = list()
    indicatorGroups_uids = list()
    indicatorGroupSets_uids = list()
    indicatorTypes_uids = list()
    legendSets_uids = list()
    organisationUnitGroups_uids = list()
    predictorGroups_uids = list()
    optionGroups_uids = list()
    optionSets_uids = list()
    cat_uids = dict()  # Contains all non DEFAULT uids of categoryOption, categories, CCs and COCs
    cat_uids['categoryOptions'] = list()
    cat_uids['categories'] = list()
    cat_uids['categoryCombos'] = list()
    cat_uids['categoryOptionCombos'] = list()
    cat_uids['categoryOptionGroups'] = list()
    cat_uids['categoryOptionGroupSets'] = list()
    cat_uids['categoryOptionsFromCOCs'] = list()
    if package_type_or_uid in ['TRK', 'EVT', 'GEN']:
        programNotificationTemplates_uids = list()
        programRuleActions_uids = list()
        if package_type_or_uid in ['TRK', 'GEN']:
            trackedEntityAttributes_uids = dict()
            trackedEntityAttributes_uids['PR'] = list()
            trackedEntityAttributes_uids['P'] = list()
            trackedEntityAttributes_uids['PI'] = list()
            trackedEntityTypes_uids = list()  # Normally only one :)
        programIndicators_uids = dict()
        programIndicators_uids['P'] = list()  # Program
        programIndicators_uids['I'] = list()
        programIndicators_uids['PRED'] = list()  # Predictor
        programIndicatorGroups_uids = list()
        programStageSections_uids = list()
    validationRules_uids = list()
    validationRuleGroups_uids = list()
    # Constants can be found in
    # programRules -> condition -> C{gYj2CUoep4O} == 2
    # programRuleActions -> data ????
    # programIndicators -> expression, filter
    constants_uids = list()
    package_admin_uid = 'vUeLeQMSwhN'

    metadata_filters = {
        "attributes": "id:in:[" + ','.join(attributes_uids) + "]",
        "categories": "code:in:[default,DEFAULT]",
        "categoryCombos": "code:in:[default,DEFAULT]",
        "categoryOptionCombos": "code:in:[default,DEFAULT]",
        "categoryOptions": "code:in:[default,DEFAULT]",
        "categoryOptionGroups": "id:in:[" + ','.join(cat_uids['categoryOptionGroups']) + "]",
        "categoryOptionGroupSets": "id:in:[" + ','.join(cat_uids['categoryOptionGroupSets']) + "]",
        "constants": "id:in:[" + ','.join(constants_uids) + "]",
        "dashboards": "code:$like:" + package_prefix,
        "dataElementGroups": "code:$like:" + package_prefix,
        "dataElements": "id:in:[" + ','.join(dataElements_in_package) + "]",
        "dataEntryForms": "id:in:[" + ','.join(dataEntryForms_uids) + "]",
        "documents": "code:$like:" + package_prefix,  # Might not be enough
        "eventCharts": "id:in:[" + ','.join(dashboard_items['eventChart']) + "]",
        "eventReports": "id:in:[" + ','.join(dashboard_items['eventReport']) + "]",
        "eventVisualizations": "id:in:[" + ','.join(dashboard_items['eventVisualization']) + "]",
        "indicatorGroupSets": "id:in:[" + ','.join(indicatorGroupSets_uids) + "]",
        "indicatorGroups": "code:$like:" + package_prefix,
        "indicators": "id:in:[" + ','.join(indicator_uids) + "]",
        "indicatorTypes": "id:in:[" + ','.join(indicatorTypes_uids) + "]",
        "jobConfigurations": "jobType:eq:PREDICTOR",
        "legendSets": "id:in:[" + ','.join(legendSets_uids) + "]",
        "maps": "id:in:[" + ','.join(dashboard_items['map']) + "]",
        "optionGroups": "optionSet.id:in:[" + ','.join(optionSets_uids) + "]",
        "options": "optionSet.id:in:[" + ','.join(optionSets_uids) + "]",
        "optionSets": "id:in:[" + ','.join(optionSets_uids) + "]",
        "organisationUnitGroups": "id:in:[" + ','.join(organisationUnitGroups_uids) + "]",
        "organisationUnitGroupSets": "organisationUnitGroups.id:in:[" + ','.join(organisationUnitGroups_uids) + "]",
        "predictors": "id:in:[" + ','.join(predictor_uids) + "]",
        "predictorGroups": "code:$like:" + package_prefix,
        "reports": "code:$like:" + package_prefix,
        "sqlViews": "code:$like:" + package_prefix,
        "visualizations": "id:in:[" + ','.join(dashboard_items['visualization']) + "]",
        "userGroups": "code:$like:" + package_prefix,
        "users": "id:eq:" + package_admin_uid
    }

    if package_type_or_uid in ['TRK', 'EVT']:
        metadata_filters.update({
            "programs": "id:in:[" + ','.join(program_uids) + "]",
            "programIndicatorGroups": "",
            "programIndicators": "program.id:in:[" + ','.join(program_uids) + "]",
            "programNotificationTemplates": "id:in:[" + ','.join(programNotificationTemplates_uids) + "]",
            "programRuleActions": "id:in:[" + ','.join(programRuleActions_uids) + "]",
            "programRules": "program.id:in:[" + ','.join(program_uids) + "]",
            "programRuleVariables": "program.id:in:[" + ','.join(program_uids) + "]",
            "programSections": "program.id:in:[" + ','.join(program_uids) + "]",
            "programStages": "program.id:in:[" + ','.join(program_uids) + "]",
            "programStageSections": "id:in:[" + ','.join(programStageSections_uids) + "]",
            # Some programs may have dataSets linked to them, like HIV
            "dataSets": "code:$like:" + package_prefix,
            "sections": "dataSet.id:[" + ','.join(dataset_uids) + "]",
            "validationNotificationTemplates": "validationRules.id:in:[" + ','.join(validationRules_uids) + "]",
            "validationRules": "id:in:[" + ','.join(validationRules_uids) + "]",
            "validationRuleGroups": "code:$like:" + package_prefix
        })
        if package_type_or_uid in ['TRK']:
            metadata_filters.update({
                "trackedEntityAttributes": "id:in:[" + ','.join(trackedEntityAttributes_uids['P']) + "]",
                "trackedEntityInstanceFilters": "program.id:in:[" + ','.join(program_uids) + "]",
                "trackedEntityTypes": "id:in:[" + ','.join(trackedEntityTypes_uids) + "]"
            })
    # Dataset
    elif package_type_or_uid == 'AGG':
        metadata_filters.update({
            "dataSets": "id:in:[" + ','.join(dataset_uids) + "]",
            "sections": "dataSet.id:[" + ','.join(dataset_uids) + "]",
            "validationNotificationTemplates": "validationRules.id:in:[" + ','.join(validationRules_uids) + "]",
            "validationRules": "id:in:[" + ','.join(validationRules_uids) + "]",
            "validationRuleGroups": "code:$like:" + package_prefix
        })
    elif package_type_or_uid == 'DSH':
        metadata_filters.update({
            "dashboards": "id:in:[" + ','.join(dashboard_uids) + "]"
        })
    elif package_type_or_uid == 'GEN':
        metadata_filters = {
            "categoryOptions": "id:in:[" + ','.join(cat_uids['categoryOptions']) + "]",
            # "categoryCombos": "id:in:[" + ','.join(cat_uids['categoryCombos']) + "]",
            "categoryOptionGroups": "code:$like:" + package_prefix,
            "dataElementGroups": "code:$like:" + package_prefix,
            "dataElements": "id:in:[" + ','.join(dataElements_in_package) + "]",
            "indicatorGroups": "code:$like:" + package_prefix,
            "indicators": "id:in:[" + ','.join(indicator_uids) + "]",
            "indicatorTypes": "code:$like:" + package_prefix,
            "optionGroups": "optionSet.id:in:[" + ','.join(optionSets_uids) + "]",
            "options": "optionSet.id:in:[" + ','.join(optionSets_uids) + "]",
            "optionSets": "id:in:[" + ','.join(optionSets_uids) + "]",
            "trackedEntityAttributes": "id:in:[" + ','.join(trackedEntityAttributes_uids['P']) + "]",
            "trackedEntityTypes": "code:$like:" + package_prefix
        }

    if len(program_uids) > 0 or len(dataset_uids) > 0 or len(dashboard_uids) or package_type_or_uid == 'GEN':

        if args.description is not None:
            package_description = args.description
        else:
            package_description = ""

        for metadata_type in reversed(metadata_import_order):
            logger.info("------------ " + metadata_type + " ------------")
            if metadata_type == "package":
                locale = "en"
                if args.only_dashboards:
                    package_type = "DSH"
                else:
                    package_type = package_type_or_uid

                name_label = package_code + '_' + package_type + \
                             '_DHIS' + api_source.version + '-' + locale

                metadata["package"] = {
                    "name": name_label,
                    "code": package_code,
                    "description": package_description,
                    "type": package_type,
                    "version": "",
                    "lastUpdated": "",
                    "DHIS2Version": api_source.version,
                    "DHIS2Build": api_source.revision,
                    "locale": locale
                }
                continue

            # --- Get the stuff -------------------------------------------------------------
            if 'code:$like' in metadata_filters[metadata_type]:
                metaobject = list()
                for prefix in all_package_prefixes:
                    # Consider ilike here for dirty packages
                    metaobject += get_metadata_element(metadata_type, 'code:$like:' + prefix)
            else:
                metaobject = get_metadata_element(metadata_type, metadata_filters[metadata_type])

            # ---  Preprocessing ---------------------------------------------------------
            # If we are matching on code, make sure we are only picking up those following the naming convention
            if "code:$like" in metadata_filters[metadata_type]:
                # There is a chance that we grabbed nothing using the package prefix. For some elements
                # like userGroups, these could be generic
                # For example, the package prefix could be COVID-19_CS, but there is also another package COVID-19_POE
                # These two packages share the same userGroups, prefixed COVID-19
                if len(metaobject) == 0 and metadata_type in ['userGroups']:
                    # Try with first to chars of the package_prefix
                    metaobject += get_metadata_element(metadata_type, 'code:$like:' + package_prefix[0:2])

            if metadata_type[:-1] in dashboard_items:
                # Update data dimension items
                dataDimension_uids = get_elements_in_data_dimension(metaobject, dataDimension_uids)

            elif metadata_type == "programIndicatorGroups":
                metaobject = remove_undesired_children(metaobject, programIndicators_uids['P'], 'programIndicators')

            elif metadata_type == "indicatorGroupSets":
                metaobject = remove_undesired_children(metaobject, indicatorGroups_uids, 'indicatorGroups')

            elif metadata_type == 'optionGroups':
                # If there are other optionGroups referenced elsewhere, add them now
                if len(optionGroups_uids) > 0:
                    current_optionGroups_uids = json_extract(metaobject, 'id')
                    # Get the new elements if any
                    new_optionGroup_uids = list(set(optionGroups_uids) - set(current_optionGroups_uids))
                    if len(new_optionGroup_uids) > 0:
                        # Update the consolidated list of optionGroups
                        optionGroups_uids = list(dict.fromkeys(optionGroups_uids + current_optionGroups_uids))
                        other_optionGroups = get_metadata_element(metadata_type, 'id:in:[' + ','.join(new_optionGroup_uids) + ']')
                        # Check for optionSets not included in the package
                        for optGroup in other_optionGroups:
                            if 'optionSet' in optGroup:
                                if optGroup['optionSet']['id'] not in optionSets_uids:
                                    logger.warning('Option Group ' + optGroup['id'] + ' references optionSet ' + optGroup['optionSet']['id'] + " which don't belong in the package")
                        # Update the options too
                        options_uids += json_extract_nested_ids(other_optionGroups, 'options')
                        metaobject += other_optionGroups
                metaobject = remove_undesired_children(metaobject, options_uids, 'options')

            elif metadata_type == "predictors":
                # Replace hardcoded UIDs for organisation Unit Levels with a placeholder
                metaobject = replace_organisation_level_with_placeholder(metaobject)
                # Remove predictorGroups in predictors which do not belong to the package
                metaobject = remove_undesired_children(metaobject, predictorGroups_uids, 'predictorGroups')

            elif metadata_type == "validationRules":
                # Remove validationRuleGroups in validationRules which do not belong to the package
                metaobject = remove_undesired_children(metaobject, validationRuleGroups_uids, 'validationRuleGroups')

            elif metadata_type == "trackedEntityAttributes":
                # Make sure the TEAs are publicly readable
                index = 0
                for index in range(0, len(metaobject)):
                    metaobject[index]["publicAccess"] = "r-------"

            elif package_type_or_uid == 'GEN':
                if metadata_type == "categoryOptions":
                    metaobject = remove_undesired_children(metaobject, cat_uids['categoryOptionGroups'],
                                                           'categoryOptionGroups')
                elif metadata_type == "options":
                    metaobject = remove_undesired_children(metaobject, [], 'optionGroups')
                elif metadata_type == "dataElements":
                    metaobject = remove_subset_from_set(metaobject, "legendSets")
                    # Delete categoryCombos from DE?
                    metaobject = remove_subset_from_set(metaobject, "categoryCombo")
                    metaobject = remove_subset_from_set(metaobject, "dataSetElements")

            elif metadata_type[:3] == 'cat':
                # Add the default uid if it does not exist yet in cat_uids list
                for cat in metaobject:
                    if cat['name'].lower() == 'default' and cat['id'] not in cat_uids[metadata_type]:
                        cat_uids[metadata_type].append(cat['id'])
                if metadata_type in cat_uids and len(cat_uids[metadata_type]) > 0:
                    logger.info('Getting extra uids for ' + metadata_type)
                    metaobject = get_metadata_element(metadata_type,
                                                      'id:in:[' + ','.join(cat_uids[metadata_type]) + ']')

                if metadata_type == "categoryOptionGroups":
                    # dhis2.py does not support multiple filters. We could use python request python to overcome this
                    # but I found complicated to have two ways of getting to the API just because of this particular scenario
                    # The issue is as follows: When using :owner, the api categoryOptions do not return the
                    # categoryOptionGroups so instead we use a filter for categoryOptionGroups as follows:
                    # filter=categoryOptions.id:in:[UID1,UID2...UIDn]
                    # the problem is that before getting to this point we may have found categoryOptionGroups
                    # used in one or more visualizations for this we would need a filter
                    # filter=id:in:[ + ','.join(cat_uids['categoryOptionGroups']) + ] with rootJunction=OR
                    # So now we know that we have the categoryOptionGroups that contain the categoryOptions
                    # which were included and we proceed to add the categoryOptionGroups already recorded
                    if len(cat_uids['categoryOptionGroups']) > 0:
                        # Get the ids already fetched
                        current_catOptGroup_uids = json_extract(metaobject, 'id')
                        # Get the uids present in one list but not the other
                        uid_list = list(set(cat_uids['categoryOptionGroups']) - set(current_catOptGroup_uids))
                        if len(uid_list) > 0:
                            metaobject += get_metadata_element('categoryOptionGroups', 'id:in"[' + ','.join(uid_list) + ']')

                    cat_opt_group_ids_to_keep = json_extract(metaobject, 'id')

                    # Remove categoryOption if it is a dashboard package
                    if package_type_or_uid == 'DSH' or args.only_dashboards:
                        metaobject = remove_subset_from_set(metaobject, 'categoryOptions')
                    else:
                        # Remove category options which are not part of the package
                        metaobject = remove_undesired_children(metaobject, cat_uids['categoryOptions'], 'categoryOptions')
                        # Check if a category option group is empty
                        for catOptGroup in metaobject:
                            if len(catOptGroup['categoryOptions']) == 0:
                                logger.warning('Category Option Group ' + catOptGroup['id'] + " is empty after trimming the category options which don't belong to the package")
                        # Remove cat opt group references from category options which are not part of the package
                        metadata['categoryOptions'] = remove_undesired_children(metadata['categoryOptions'],
                                                                                cat_opt_group_ids_to_keep,
                                                                                'categoryOptionGroups')

                elif metadata_type == "categoryOptionGroupSets":
                    # We need to remove the categoryOptionGroupSets which contain categoryOptionGroups not belonging to the package
                    new_metaobject = list()
                    cat_opt_group_set_ids_to_keep = list()
                    for catOptGroupSet in metaobject:
                        valid_cat_opt_group_set = True
                        for catOptGroup in catOptGroupSet['categoryOptionGroups']:
                            if catOptGroup['id'] not in cat_uids['categoryOptionGroups']:
                                valid_cat_opt_group_set = False
                                break
                        if valid_cat_opt_group_set:
                            new_metaobject.append(catOptGroupSet)
                            cat_opt_group_set_ids_to_keep.append(catOptGroupSet['id'])
                    metadata['categoryOptionGroups'] = remove_undesired_children(metadata['categoryOptionGroups'],
                                                                                 cat_opt_group_set_ids_to_keep,
                                                                                 'groupSets')
                    metaobject = new_metaobject

                    # categoryOptionGroups and categoryOptionGroupSets reference each other, so also do this clean up
                    metaobject = remove_undesired_children(metaobject,
                                                           cat_opt_group_ids_to_keep,
                                                           'categoryOptionGroups')
            elif metadata_type == "organisationUnitGroupSets":
                metaobject = remove_undesired_children(metaobject, organisationUnitGroups_uids,
                                                       'organisationUnitGroups')
                metaobject = remove_subset_from_set(metaobject, 'items')

            elif metadata_type == "jobConfigurations":
                job_configs_to_include = list()
                for jobConfig in metaobject:
                    job_config_in_the_package = True
                    if 'predictors' in jobConfig['jobParameters']:
                        for predictor_uid in jobConfig['jobParameters']['predictors']:
                            if predictor_uid not in predictor_uids:
                                job_config_in_the_package = False
                                break
                    if job_config_in_the_package and 'predictorGroups' in jobConfig['jobParameters']:
                        for predictorGroup_uid in jobConfig['jobParameters']['predictorGroups']:
                            if predictorGroup_uid not in predictorGroups_uids:
                                job_config_in_the_package = False
                                break
                    if job_config_in_the_package:
                        job_configs_to_include.append(jobConfig)
                metaobject = job_configs_to_include

            # Update dataframe reports
            update_last_updated(metaobject, metadata_type)

            # --- Clean up - remove lastUpdated, created, etc... ------------------------
            metaobject = clean_metadata(metaobject)
            if metadata_type == 'users':
                metaobject = remove_subset_from_set(metaobject, 'userGroups')
                metaobject = remove_subset_from_set(metaobject, 'userGroupAccesses')

            # --- Checks - validation ----------------------------------------------------------------
            ## Remove orgunits
            org_units_assigned = json_extract_nested_ids(metaobject, 'organisationUnits')
            if len(org_units_assigned) > 0:
                if metadata_type in ['eventReports', 'eventCharts', 'eventVisualizations', 'visualizations']:
                    metaobject = check_and_replace_root_ou_assigned(metaobject)
                else:
                    logger.warning('There are org units assigned... Removing')
                    metaobject = remove_subset_from_set(metaobject, 'organisationUnits')

            ## Warn about relative Periods not being used
            if metadata_type in ['eventReports', 'eventCharts', 'eventVisualizations', 'visualizations', 'maps']:
                for dashboard_item in metaobject:
                    if 'relativePeriods' in dashboard_item:
                        at_least_one_relative_period = False
                        # Loop all the keys in the dictionary until you find one set to True
                        # Every key represents a relative period type, such as thisYear, yesterday, last4Weeks...
                        for relative_period in dashboard_item['relativePeriods']:
                            if dashboard_item['relativePeriods'][relative_period]:
                                at_least_one_relative_period = True
                                break
                        if not at_least_one_relative_period:
                            logger.warning('Dashboard item of type ' + metadata_type + ' with UID = ' + dashboard_item[
                                'id'] + ' does not have any relative period configured. Please review')

            ## Check sharing
            ### With userGroups
            if metadata_type != 'userGroups':  # userGroups are processed in post-processing
                metaobject = check_sharing(metaobject)
            # else:
            #    metaobject = check_sharing(metaobject, ['userGroupAccesses'])

            ## Custom checks
            if package_type_or_uid in ['TRK', 'EVT']:
                if metadata_type == "eventVisualizations":
                    # Get number of eventVisualizations assigned to the program(s) and compare
                    eventVisualizations = get_metadata_element(metadata_type, "program.id:in:[" + ','.join(program_uids) + "]")
                    if len(eventVisualizations) != len(metaobject):
                        logger.warning(
                            "The program has " + str(len(eventVisualizations)) + " eventVisualizations assigned to it, but only " +
                            str(len(metaobject)) + " were found in the dashboards belonging to the program")
                elif metadata_type == "trackedEntityAttributes":
                    # Our reference for trackedEntityAttributes to use are those assigned to the Program
                    # Check TEAs used in program rules
                    diff = list(set(trackedEntityAttributes_uids['PR']).difference(trackedEntityAttributes_uids['P']))
                    if len(diff) > 0:
                        logger.error("Program rules use trackedEntityAttributes not assigned to the program: "
                                     + str(diff))
                        total_errors += 1
                        check_issues_with_program_rules(metadata, diff, "TEA")
                    # Check TEAs used in Program Indicators
                    diff = list(set(trackedEntityAttributes_uids['PI']).difference(trackedEntityAttributes_uids['P']))
                    if len(diff) > 0:
                        logger.error("Program indicators use trackedEntityAttributes not included in the program: "
                                     + str(diff))
                        total_errors += 1
                    # Check TEAs used in Indicators
                    diff = list(set(trackedEntityAttributes_uids['I']).difference(trackedEntityAttributes_uids['P']))
                    if len(diff) > 0:
                        logger.error("Indicators use trackedEntityAttributes not included in the program: "
                                     + str(diff))
                        total_errors += 1
                    # Note: including programSections (PS), we are assuming that the trackedEntityAttributes (TEAs)
                    # referenced by the PS(s) are part of the program TEAs. The tests carried out point in that
                    # direction so initially there is no need to check the programSections TEAs

                    # Check TEAs used in Analytics
                    diff_data_dimension = list(
                        set(dataDimension_uids['attribute']).difference(trackedEntityAttributes_uids['P']))
                    if len(diff_data_dimension) > 0:
                        logger.warning("Data dimension in analytics use TEAs not included in the package: "
                                       + str(diff_data_dimension) + "... Adding them")
                        total_errors += 1
                        trackedEntityAttributes_in_data_dimension = get_metadata_element(metadata_type, "id:in:[" + ','.join(
                            diff_data_dimension) + "]")
                        trackedEntityAttributes_in_data_dimension = check_sharing(trackedEntityAttributes_in_data_dimension)
                        trackedEntityAttributes_in_data_dimension = clean_metadata(trackedEntityAttributes_in_data_dimension)
                        metaobject += trackedEntityAttributes_in_data_dimension
                        trackedEntityAttributes_uids['P'] += diff_data_dimension

                elif metadata_type == "programIndicators":
                    # Get UIDs to analyze PIs included in the Program (P) VS the ones used in num/den of indicators
                    # And also use this list to cleanup the programIndicatorGroups
                    for programIndicator in metaobject:
                        programIndicators_uids['P'].append(programIndicator['id'])
                    # Check PIs used in Indicators
                    diff = list(set(programIndicators_uids['I']).difference(programIndicators_uids['P']))
                    if len(diff) > 0:
                        # Turning this error into a warning due to an issue with MAL FOCI and MAL CS
                        logger.warning("Indicators use programIndicators not included in the program: "
                                       + str(diff))
                        # total_errors += 1
                        for uid in diff:
                            ind_num = api_source.get('indicators',
                                                     params={"fields": "id,name",
                                                             "filter": "numerator:like:" + uid}).json()['indicators']
                            ind_den = api_source.get('indicators',
                                                     params={"fields": "id,name",
                                                             "filter": "denominator:like:" + uid}).json()['indicators']
                            indicators = ind_num + ind_den
                            if len(indicators) > 0:
                                logger.info('! ' + ' programIndicator ' + uid + ' used in indicator ')
                                for ind in indicators:
                                    logger.info('   ' + ind['id'] + ' - ' + ind['name'])

                    # Check PIs used in Predictors (we give less information because using predictors is rare)
                    diff = list(set(programIndicators_uids['PRED']).difference(programIndicators_uids['P']))
                    if len(diff) > 0:
                        logger.error("Predictors use programIndicators not included in the program: "
                                     + str(diff))
                        total_errors += 1

                # Check TEAs used in Analytics
                diff_data_dimension = list(
                    set(dataDimension_uids['attribute']).difference(trackedEntityAttributes_uids['P']))
                if len(diff_data_dimension) > 0:
                    logger.warning("Data dimension in analytics use TEAs not included in the package: "
                                   + str(diff_data_dimension) + "... Adding them")
                    total_errors += 1
                    trackedEntityAttributes_in_data_dimension = get_metadata_element(metadata_type, "id:in:[" + ','.join(
                        diff_data_dimension) + "]")
                    trackedEntityAttributes_in_data_dimension = check_sharing(trackedEntityAttributes_in_data_dimension)
                    trackedEntityAttributes_in_data_dimension = clean_metadata(trackedEntityAttributes_in_data_dimension)
                    metaobject += trackedEntityAttributes_in_data_dimension
                    trackedEntityAttributes_uids['P'] += diff_data_dimension

            elif metadata_type == "programIndicators":
                # Get UIDs to analyze PIs included in the Program (P) VS the ones used in num/den of indicators
                # And also use this list to cleanup the programIndicatorGroups
                for programIndicator in metaobject:
                    programIndicators_uids['P'].append(programIndicator['id'])
                # Check PIs used in Indicators
                diff = list(set(programIndicators_uids['I']).difference(programIndicators_uids['P']))
                if len(diff) > 0:
                    # Turning this error into a warning due to an issue with MAL FOCI and MAL CS
                    logger.warning("Indicators use programIndicators not included in the program: "
                                   + str(diff))
                    # total_errors += 1
                    for uid in diff:
                        ind_num = api_source.get('indicators',
                                                 params={"fields": "id,name",
                                                         "filter": "numerator:like:" + uid}).json()['indicators']
                        ind_den = api_source.get('indicators',
                                                 params={"fields": "id,name",
                                                         "filter": "denominator:like:" + uid}).json()['indicators']
                        indicators = ind_num + ind_den
                        if len(indicators) > 0:
                            logger.info('! ' + ' programIndicator ' + uid + ' used in indicator ')
                            for ind in indicators:
                                logger.info('   ' + ind['id'] + ' - ' + ind['name'])

                # Check PIs used in Predictors (we give less information because using predictors is rare)
                diff = list(set(programIndicators_uids['PRED']).difference(programIndicators_uids['P']))
                if len(diff) > 0:
                    logger.error("Predictors use programIndicators not included in the program: "
                                 + str(diff))
                    total_errors += 1

                # Check PIs used in Analytics
                diff_data_dimension = list(
                    set(dataDimension_uids['programIndicator']).difference(programIndicators_uids['P']))
                if len(diff_data_dimension) > 0:
                    logger.warning("Data dimension in analytics use programIndicators not included in the package: "
                                   + str(diff_data_dimension) + "... Adding them")
                    total_errors += 1
                    programIndicators_in_data_dimension = get_metadata_element(metadata_type, "id:in:[" + ','.join(
                        diff_data_dimension) + "]")
                    programIndicators_in_data_dimension = check_sharing(programIndicators_in_data_dimension)
                    programIndicators_in_data_dimension = clean_metadata(programIndicators_in_data_dimension)
                    metaobject += programIndicators_in_data_dimension
                    programIndicators_uids['P'] += diff_data_dimension

            elif metadata_type == "programNotificationTemplates":
                # Check that the number of pnt with the program prefix is not greater
                pnt_with_program_prefix = list()
                for prefix in all_package_prefixes:
                    pnt_with_program_prefix += get_metadata_element(metadata_type, "name:like:" + prefix)
                if len(pnt_with_program_prefix) > len(programNotificationTemplates_uids):
                    pnt_with_program_prefix_uids = list()
                    for pnt in pnt_with_program_prefix:
                        if (pnt['name'].find(package_prefix)) == 0:
                            pnt_with_program_prefix_uids.append(pnt['id'])

                    diff = list(set(pnt_with_program_prefix_uids).difference(programNotificationTemplates_uids))
                    if len(diff) > 0:
                        logger.warning(
                            "There are programNotificationTemplates with package prefix " + package_prefix +
                            " not used in any program rule action or program: " + str(diff))

                # Check for userGroups used which are not included in the package
                new_userGroups_uids = list()
                for PNT in metaobject:
                    if 'recipientUserGroup' in PNT and PNT['recipientUserGroup']['id'] not in userGroups_uids and \
                            PNT['recipientUserGroup']['id'] not in new_userGroups_uids:
                        new_userGroups_uids.append(PNT['recipientUserGroup']['id'])
                if len(new_userGroups_uids) > 0:
                    # Get those user Groups
                    new_userGroups = get_metadata_element('userGroups',
                                                          'id:in:[' + ','.join(new_userGroups_uids) + ']')
                    logger.warning(
                        "ProgramNotificationTemplates use a userGroup recipient not included in the package... ADDING")
                    for UG in new_userGroups:
                        logger.warning(" ! " + UG['id'] + " - " + UG['name'])
                    new_userGroups = clean_metadata(new_userGroups)
                    # Remove all users from the group
                    new_userGroups = remove_subset_from_set(new_userGroups, 'users')
                    # Add userGroups and check sharing
                    metadata['userGroups'] += new_userGroups
                    # Before calling check_sharing, update the userGroup uids global variable
                    userGroups_uids += new_userGroups_uids
                    metadata['userGroups'] = check_sharing(metadata['userGroups'])

            elif metadata_type == "validationNotificationTemplates":
                # Check for userGroups used which are not included in the package
                new_userGroups_uids = list()
                for VNT in metaobject:
                    if 'recipientUserGroup' in VNT and VNT['recipientUserGroup']['id'] not in userGroups_uids and \
                            VNT['recipientUserGroup']['id'] not in new_userGroups_uids:
                        new_userGroups_uids.append(VNT['recipientUserGroup']['id'])
                if len(new_userGroups_uids) > 0:
                    # Get those user Groups
                    new_userGroups = get_metadata_element('userGroups',
                                                          'id:in:[' + ','.join(new_userGroups_uids) + ']')
                    logger.warning(
                        "ValidationNotificationTemplates use a userGroup recipient not included in the package... ADDING")
                    for UG in new_userGroups:
                        logger.warning(" ! " + UG['id'] + " - " + UG['name'])
                    new_userGroups = clean_metadata(new_userGroups)
                    # Remove all users from the group
                    new_userGroups = remove_subset_from_set(new_userGroups, 'users')
                    # Add userGroups and check sharing
                    metadata['userGroups'] += new_userGroups
                    # Before calling check_sharing, update the userGroup uids global variable
                    userGroups_uids += new_userGroups_uids
                    metadata['userGroups'] = check_sharing(metadata['userGroups'])

            elif metadata_type == "dataEntryForms":
                for custom_form in metaobject:
                    if 'htmlCode' in custom_form:
                        all_data_entry_uids = findall(r'[a-zA-Z0-9]{11}\-([a-zA-Z0-9]{11})\-val',
                                                      custom_form['htmlCode'])
                        diff = list(set(all_data_entry_uids).difference(dataElements_in_package))
                        if len(diff) > 0:
                            diff_with_coc = list(set(diff).difference(cat_uids['categoryOptionCombos']))
                            if len(diff_with_coc) > 0:
                                for element_uid in diff_with_coc:
                                    element = api_source.get('identifiableObjects/' + element_uid).json()
                                    if 'code' in element and element['code'].lower() == 'default':
                                        diff_with_coc.remove(element_uid)
                            if len(diff_with_coc) > 0:
                                logger.warning('COC Elements used in dataEntryForm ' + custom_form[
                                    'id'] + ': ' + str(diff_with_coc) + ' are not part of the package')

            elif metadata_type == "dataElements":
                diff_ps = list()
                if package_type_or_uid in ['TRK', 'EVT']:
                    # Compare those dataElements with those assigned to PS -> Is there a dataElement missing?
                    diff_ps = list(set(dataElements_uids['PS']).difference(dataElements_in_package))
                    if len(diff_ps) > 0:
                        logger.warning(
                            "DataElements assigned to the Program Stage(s) in package: " + str(
                                diff_ps) + ' are not assigned to any dataElementGroup... Adding them to the package')
                    # Check DEs used in Program Rules VS what has been so far included in the package
                    diff = list(set(dataElements_uids['PR']).difference(dataElements_in_package))
                    if len(diff) > 0:
                        logger.error("Program rules use dataElements not included in the program: "
                                     + str(diff))
                        total_errors += 1
                        check_issues_with_program_rules(metadata, diff, "DE")
                    # Check DE assigned to the Program Stages VS Program Stage Sections
                    if len(dataElements_uids['PS']) < len(dataElements_uids['PSS']):
                        logger.error("Program stage sections use dataElements not assigned to any programStage: "
                                     + str(list(set(dataElements_uids['PSS']).difference(dataElements_uids['PS']))))
                        total_errors += 1
                    elif len(dataElements_uids['PS']) > len(dataElements_uids['PSS']):
                        logger.warning("Program stage use dataElements not assigned to any programStageSection: "
                                       + str(list(set(dataElements_uids['PS']).difference(dataElements_uids['PSS']))))
                    # Check DEs used in Program Indicators
                    diff = list(set(dataElements_uids['PI']).difference(dataElements_in_package))
                    if len(diff) > 0:
                        logger.error("Program indicators use dataElements not included in the package: "
                                     + str(diff))
                        total_errors += 1
                        for uid in diff:
                            PIs = api_source.get('programIndicators',
                                                 params={"fields": "id,name",
                                                         "filter": "filter:like:" + uid}).json()['programIndicators']
                            logger.info('! ' + ' dataElement ' + uid + ' used in filters of ')
                            for pi in PIs:
                                logger.info('   ' + pi['id'] + ' - ' + pi['name'])
                # Dataset
                # Compare those dataElements with those assigned to DS -> Is there a dataElement missing?
                diff_ds = list(set(dataElements_uids['DS']).difference(dataElements_in_package))
                if len(diff_ds) > 0:
                    logger.warning(
                        "DataElements assigned to the DataSet(s) in package: " + str(
                            diff_ds) + ' are not assigned to any dataElementGroup... Adding them to the package')

                diff = list(set(dataElements_uids['VR']).difference(dataElements_in_package))
                if len(diff) > 0:
                    logger.error("Validation rules use dataElements not included in the program: "
                                 + str(diff))
                    total_errors += 1
                # Check DEs used in Indicators
                diff_ind = list(set(dataElements_uids['I']).difference(dataElements_in_package))
                if len(diff_ind) > 0:
                    # This should maybe be moved to Pre-processing
                    # In pre-processing we add ot the package those DEs with package prefix
                    # here we add the package those used in indicators
                    logger.warning("Indicators use dataElements not included in the package: "
                                   + str(diff_ind) + "... Adding them")
                # Check DEs used in Predictors
                diff_pred = list(set(dataElements_uids['PRED']).difference(dataElements_in_package))
                if len(diff_pred) > 0:
                    # This should maybe be moved to Pre-processing
                    # In pre-processing we add ot the package those DEs with package prefix
                    # here we add the package those used in indicators
                    logger.warning("Predictors use dataElements not included in the package: "
                                   + str(diff_pred) + "... Adding them")

                # In this case, we add the DEs... Why? Program Indicators have a direct reference to the program
                # they belong to... So we expect them to use DEs which are part of the program (the UI does not
                # let you choose DEs outside the program in principle)
                # But indicators rely on PREFIX and are much more open to using other DEs

                diff = list(dict.fromkeys(diff_ps + diff_ds + diff_ind + diff_pred))
                if len(diff) > 0:
                    dataElements_in_indicators = get_metadata_element(metadata_type, "id:in:[" + ','.join(diff) + "]")
                    dataElements_in_indicators = check_sharing(dataElements_in_indicators)
                    dataElements_in_indicators = clean_metadata(dataElements_in_indicators)
                    metaobject += dataElements_in_indicators

                    dataElements_in_package += diff

                # Check DEs used in Analytics
                diff_data_dimension = list(set(dataDimension_uids['dataElement']).difference(dataElements_in_package))
                if len(diff_data_dimension) > 0:
                    logger.warning("Data dimension in analytics use dataElements not included in the package: "
                                   + str(diff_data_dimension) + "... Adding them")
                    dataElements_in_data_dimension = get_metadata_element(metadata_type, "id:in:[" + ','.join(
                        diff_data_dimension) + "]")
                    dataElements_in_data_dimension = check_sharing(dataElements_in_data_dimension)
                    dataElements_in_data_dimension = clean_metadata(dataElements_in_data_dimension)
                    metaobject += dataElements_in_data_dimension
                    dataElements_in_package += diff_data_dimension

                # Clean dataElementGroups
                if len(metadata['dataElementGroups']) > 0:
                    metadata['dataElementGroups'] = remove_undesired_children(metadata['dataElementGroups'],
                                                                              dataElements_in_package,
                                                                              'dataElements')
                # Remove dataElementGroups in dataElements which do not belong to the package
                metaobject = remove_undesired_children(metaobject, dataElementsGroups_uids, 'dataElementGroups')

            elif metadata_type == 'indicators':
                # Check Indicators used in Analytics
                # It is possible that indicators_uids is empty, because we match using prefix / indicatorGroup
                # So let's initialize it to compare to the indicators used in a dashboard and see if we missed something
                for indicator in metaobject:
                    indicator_uids.append(indicator['id'])
                diff_data_dimension = list(set(dataDimension_uids['indicator']).difference(indicator_uids))
                if len(diff_data_dimension) > 0:
                    logger.warning("Data dimension in analytics use indicators not included in the package: "
                                   + str(diff_data_dimension) + "... Adding them")
                    indicators_in_data_dimension = get_metadata_element(metadata_type,
                                                                        "id:in:[" + ','.join(diff_data_dimension) + "]")
                    indicators_in_data_dimension = check_sharing(indicators_in_data_dimension)
                    indicators_in_data_dimension = clean_metadata(indicators_in_data_dimension)
                    metaobject += indicators_in_data_dimension
                    indicator_uids += diff_data_dimension

                diff_data_set = list(set(dataSetElements_uids['indicator']).difference(indicator_uids))
                if len(diff_data_set) > 0:
                    logger.warning("DataSets use indicators not included in the package: "
                                   + str(diff_data_set) + "... Adding them")
                    indicators_in_dataset = get_metadata_element(metadata_type,
                                                                 "id:in:[" + ','.join(diff_data_set) + "]")
                    indicators_in_dataset = check_sharing(indicators_in_dataset)
                    indicators_in_dataset = clean_metadata(indicators_in_dataset)
                    metaobject += indicators_in_dataset
                    indicator_uids += diff_data_dimension

                # Remove indicatorGroups in indicators which do not belong to the package
                metaobject = remove_undesired_children(metaobject, indicatorGroups_uids, 'indicatorGroups')

            elif metadata_type == 'categoryOptions':
                # Compare the categoryOptions to include at this point with those coming from COCs
                # If the COCs have more cat options, warn the user about orphan COCs and try to clean it up
                current_category_options = json_extract(metaobject, 'id')
                diff_cat_opt = list(set(cat_uids['categoryOptionsFromCOCs']).difference(current_category_options))
                if len(diff_cat_opt) > 0:
                    logger.warning("Orphan COCs are included in the package. Please run Maintenance in the instance")
                    for COC in metadata['categoryOptionCombos']:
                        COC_uid = COC['id']
                        new_cat_options = list()
                        for catOpt in COC['categoryOptions']:
                            if catOpt['id'] not in current_category_options:
                                logger.warning('  categoryOption ' + catOpt['id'] + ' in COC ' + COC['id'] + ' does not belong in the package')
                            else:
                                new_cat_options.append(catOpt)
                        COC['categoryOptions'] = new_cat_options

            # --- Add to metadata --------------------------------------------------------
            metadata[metadata_type] = metaobject
            logger.info(str(len(metadata[metadata_type])) + " added to the package")

            # --- Post processing ---------------------------------------------------------
            if metadata_type == "userGroups":
                # Store the ids
                ug_names = list()
                for ug in metadata[metadata_type]:
                    userGroups_uids.append(ug['id'])
                    ug_names.append(ug['name'])
                logger.info(', '.join(ug_names))
                metadata[metadata_type] = check_sharing(metadata[metadata_type])
            elif metadata_type == "dashboards":
                # The following loop compiles all ids by type of dashboard items
                # for example, let's get all ids of all visualisations used in all dashboards of this package
                for dashboard in metaobject:
                    items = get_dashboard_elements(dashboard)
                    for elem in ['visualization', 'eventReport', 'eventChart', 'map', 'eventVisualization']:
                        if elem in dashboard_items:
                            dashboard_items[elem] = dashboard_items[elem] + items[elem]
                            # Make sure the list of ID is unique
                            dashboard_items[elem] = list(dict.fromkeys(dashboard_items[elem]))
                # Update the filters
                for elem in ['visualization', 'eventReport', 'eventChart', 'map', 'eventVisualization']:
                    metadata_filters[elem + 's'] = "id:in:[" + ','.join(dashboard_items[elem]) + "]"
            elif metadata_type in ['visualizations', 'maps']:
                # Add legendSets
                legendSets_uids += json_extract_nested_ids(metaobject, 'legendSets')
                legendSets_uids += json_extract_nested_ids(metaobject, 'legendSet')
                # See if there is a reference to a categoryOption Group and/or Set
                cat_uids['categoryOptionGroups'] += json_extract_nested_ids(metaobject, 'categoryOptionGroups')
                cat_uids['categoryOptionGroupSets'] += json_extract_nested_ids(metaobject, 'categoryOptionGroupSet')
                organisationUnitGroups_uids += json_extract_nested_ids(metaobject, 'itemOrganisationUnitGroups')
                if len(organisationUnitGroups_uids) > 0:
                    metadata_filters["organisationUnitGroups"] = "id:in:[" + ','.join(organisationUnitGroups_uids) + "]"

            elif metadata_type == "programRules":
                programRuleActions_uids = json_extract_nested_ids(metaobject, 'programRuleActions')
                # Update the filters
                metadata_filters["programRuleActions"] = "id:in:[" + ','.join(programRuleActions_uids) + "]"
                # Get constants:
                constants_uids += get_hardcoded_values_in_fields(metaobject, 'constants', 'condition')
            elif metadata_type == "programRuleActions":
                # Scan for DE / TEA used in programRuleActions. We will check if they are assigned to the program
                dataElements_uids['PR'] += json_extract_nested_ids(metaobject, 'dataElement')
                # Scan for option groups
                optionGroups_uids += json_extract_nested_ids(metaobject, 'optionGroup')
                if package_type_or_uid == 'TRK':
                    trackedEntityAttributes_uids['PR'] += json_extract_nested_ids(metaobject, 'trackedEntityAttribute')
                # There is a field templateUid which may not be null and might reference a programNotificationTemplate
                # which should be part of a program / programStage, so no need to check it for now
            elif metadata_type == "programRuleVariables":
                # Scan for DE / TEA used in programRuleVariables. We will check if they are assigned to the program
                dataElements_uids['PR'] += json_extract_nested_ids(metaobject, 'dataElement')
                if package_type_or_uid == 'TRK':
                    trackedEntityAttributes_uids['PR'] += json_extract_nested_ids(metaobject, 'trackedEntityAttribute')
            elif metadata_type == "programIndicators":
                programIndicatorGroups_uids = json_extract_nested_ids(metaobject, 'programIndicatorGroups')
                metadata_filters["programIndicatorGroups"] = "id:in:[" + ','.join(programIndicatorGroups_uids) + "]"
                constants_uids += get_hardcoded_values_in_fields(metaobject, 'constants', ['expression', 'filter'])
                dataElements_uids['PI'] = get_hardcoded_values_in_fields(metaobject, 'dataElements_prgInd',
                                                                         ['expression', 'filter'])
                if package_type_or_uid == 'TRK':
                    trackedEntityAttributes_uids['PI'] = get_hardcoded_values_in_fields(metaobject,
                                                                                        'trackedEntityAttributes',
                                                                                        ['expression', 'filter'])
                legendSets_uids += json_extract_nested_ids(metaobject, 'legendSets')
            elif metadata_type == "programStages":
                # Scan for DE used in program stage. We will check against program stage sections
                dataElements_uids['PS'] = json_extract_nested_ids(metaobject, 'dataElement')
                programStageSections_uids = json_extract_nested_ids(metaobject, 'programStageSections')
                dataEntryForms_uids = json_extract_nested_ids(metaobject, 'dataEntryForm')
                programNotificationTemplates_uids += json_extract_nested_ids(metaobject, 'notificationTemplates')
                # Update the filters
                metadata_filters["programStageSections"] = "id:in:[" + ','.join(programStageSections_uids) + "]"
                if len(dataElements_uids['PRED']) == 0:
                    metadata_filters["dataElements"] = "id:in:[" + ','.join(dataElements_uids['PS']) + "]"
                else:
                    # Add also the DEs used in predictors
                    metadata_filters["dataElements"] = "id:in:[" + ','.join(
                        dataElements_uids['PS'] + dataElements_uids['PRED']) + "]"
                metadata_filters["dataEntryForms"] = "id:in:[" + ','.join(dataEntryForms_uids) + "]"
            elif metadata_type == "programStageSections":
                # Please note that for PSS the key is dataElements with "s"
                dataElements_uids['PSS'] = json_extract_nested_ids(metaobject, 'dataElements')
            elif metadata_type == "programs":
                if package_type_or_uid == 'TRK':
                    trackedEntityTypes_uids = json_extract_nested_ids(metaobject, 'trackedEntityType')
                    trackedEntityAttributes_uids['P'] = json_extract_nested_ids(metaobject, 'trackedEntityAttribute')
                    # Update filter
                    metadata_filters["trackedEntityTypes"] = "id:in:[" + ','.join(trackedEntityTypes_uids) + "]"
                    metadata_filters["trackedEntityAttributes"] = "id:in:[" + ','.join(
                        trackedEntityAttributes_uids['P']) + "]"
                # At this point we have collected all possible references to constants, so update that filter too
                metadata_filters["constants"] = "id:in:[" + ','.join(list(dict.fromkeys(constants_uids))) + "]"
                programNotificationTemplates_uids += json_extract_nested_ids(metaobject, 'notificationTemplates')
                metadata_filters['programNotificationTemplates'] = "id:in:[" + ','.join(
                    programNotificationTemplates_uids) + "]"
                # EVENT programs may have a categoryCombo field
                if 'categoryCombo' in program and is_valid_uid(program['categoryCombo']['id']):
                    cat_uids = get_category_elements(program['categoryCombo']['id'], cat_uids)
            elif metadata_type == "dataSets":
                ## Remove interpretations
                organisationUnits = json_extract_nested_ids(metaobject, 'organisationUnits')
                if len(organisationUnits) > 0:
                    logger.warning('There are organisationUnits assgined to the dataSet... Removing')
                    metadata['dataSets'] = remove_subset_from_set(metadata['dataSets'], 'organisationUnits')
                sections_uids = list()
                categoryCombos_uids = list()
                for ds in metaobject:
                    sections_uids += json_extract_nested_ids(ds, 'sections')
                    if 'dataEntryForm' in ds:
                        dataEntryForms_uids += json_extract_nested_ids(ds, 'dataEntryForm')
                    if 'categoryCombo' in ds and is_valid_uid(ds['categoryCombo']['id']):
                        categoryCombos_uids.append(ds['categoryCombo']['id'])
                    if 'legendSets' in ds:
                        legendSets_uids += json_extract_nested_ids(ds, 'legendSet')
                    if 'indicators' in ds:
                        dataSetElements_uids['indicator'] += json_extract_nested_ids(ds, 'indicators')
                    if 'dataSetElements' in ds:
                        dataElements_uids['DS'] += json_extract_nested_ids(ds['dataSetElements'], 'dataElement')
                        # Get possible categoryCombos
                        categoryCombos_uids += json_extract_nested_ids(ds['dataSetElements'], 'categoryCombo')

                    if 'notificationRecipients' in ds and ds['notificationRecipients']['id'] not in userGroups_uids:
                        logger.warning("dataSet use a userGroup recipient not included in the package... ADDING")
                        new_userGroup = get_metadata_element('userGroups',
                                                             'id:in:[' + ds['notificationRecipients']['id'] + ']')
                        logger.warning(" ! " + new_userGroup[0]['id'] + " - " + new_userGroup[0]['name'])
                        new_userGroup = clean_metadata(new_userGroup)
                        # Remove all users from the group
                        new_userGroup = remove_subset_from_set(new_userGroup, 'users')
                        # Add userGroups and check sharing
                        metadata['userGroups'] += new_userGroup
                        # Before calling check_sharing, update the userGroup uids global variable
                        userGroups_uids += new_userGroup[0]['id']
                        metadata['userGroups'] = check_sharing(metadata['userGroups'])
                    if 'compulsoryDataElementOperands' in ds:
                        # Search for categoryOptionCombo, legendSets
                        for operand in ds['compulsoryDataElementOperands']:
                            if 'legendSets' in operand:
                                legendSets_uids += json_extract_nested_ids(ds, 'legendSet')
                            if 'categoryOptionCombo' in operand and \
                                    operand['categoryOptionCombo']['id'] not in cat_uids['categoryOptionCombos']:
                                add_category_option_combo(operand['categoryOptionCombo']['id'], cat_uids)
                for cc in categoryCombos_uids:
                    cat_uids = get_category_elements(cc, cat_uids)
                metadata_filters["dataEntryForms"] = "id:in:[" + ','.join(dataEntryForms_uids) + "]"
                metadata_filters['sections'] = "dataSet.id:in:[" + ','.join(dataset_uids) + "]"
            elif metadata_type == "dataElements":
                # Scan for optionSets used
                optionSets_uids += json_extract_nested_ids(metaobject, 'optionSet')
                # Update the filters
                metadata_filters["optionSets"] = "id:in:[" + ','.join(optionSets_uids) + "]"
                metadata_filters["optionGroups"] = "optionSet.id:in:[" + ','.join(optionSets_uids) + "]"
                metadata_filters["options"] = "optionSet.id:in:[" + ','.join(optionSets_uids) + "]"
                legendSets_uids += json_extract_nested_ids(metaobject, 'legendSets')
                # Check if DE uses categoryCombo
                for de in metaobject:
                    if 'categoryCombo' in de:
                        cat_uids = get_category_elements(de['categoryCombo']['id'], cat_uids)
                        # GEN PACKAGE
                        # metadata_filters["categoryCombos"] = "id:in:[" + ','.join(
                        #     cat_uids['categoryCombos']) + "]"

            elif metadata_type == "trackedEntityTypes":
                # Scan for trackedEntityAttributes used
                trackedEntityAttributes_uids['TET'] = json_extract_nested_ids(metaobject, 'trackedEntityAttribute')
                # Check for Tracked Entity Attributes in TET not used in the program
                # This check happens here because we are processing TET before trackedEntityAttributes
                # If there are TEAs used in the TET which are not in the program, we need to add them and update the list
                # so when we fetch the TEAs we get all the TEAs needed for the package
                diff_att = list(set(trackedEntityAttributes_uids['TET']).difference(trackedEntityAttributes_uids['P']))
                if len(diff_att) > 0:
                    logger.warning("Tracked Entity Type has TEAs not used in the program: " + str(diff_att))
                    # Add them to the total for the program and update the filter
                    trackedEntityAttributes_uids['P'] += diff_att
                    metadata_filters["trackedEntityAttributes"] = "id:in:[" + ','.join(
                        trackedEntityAttributes_uids['P']) + "]"
                if package_type_or_uid == 'GEN':
                    # Delete GNTR00_TEAS only used to group metadata
                    new_tet_list = list()
                    codes_to_remove = list()
                    for tet in metaobject:
                        if 'name' not in tet or 'GEN' not in tet['name']:
                            new_tet_list.append(tet)
                        else:
                            if 'code' in tet:
                                codes_to_remove.append(tet['code'])
                    metadata["trackedEntityTypes"] = new_tet_list
                    df_report_lastUpdated = df_report_lastUpdated[~df_report_lastUpdated.code.isin(codes_to_remove)]
            elif metadata_type == "trackedEntityAttributes":
                # Scan for optionSets used
                optionSets_uids += json_extract_nested_ids(metaobject, 'optionSet')
                # Update the filters not needed because dataElements will take care of it
                legendSets_uids += json_extract_nested_ids(metaobject, 'legendSets')
            elif metadata_type == "indicators":
                if package_type_or_uid in ['TRK', 'EVT']:
                    if package_type_or_uid == 'TRK':
                        trackedEntityAttributes_uids['I'] = get_hardcoded_values_in_fields(metaobject,
                                                                                           'trackedEntityAttributes',
                                                                                           ['numerator', 'denominator'])
                    programIndicators_uids['I'] = get_hardcoded_values_in_fields(metaobject,
                                                                                 'programIndicators',
                                                                                 ['numerator', 'denominator'])
                constants_uids += get_hardcoded_values_in_fields(metaobject, 'constants', ['numerator', 'denominator'])
                dataElements_uids['I'] = get_hardcoded_values_in_fields(metaobject, 'dataElements_ind',
                                                                        ['numerator', 'denominator'])
                hardcoded_cocs = get_hardcoded_values_in_fields(metaobject, 'categoryOptionCombos',
                                                                ['numerator', 'denominator'])
                for coc in hardcoded_cocs:
                    if coc not in cat_uids['categoryOptionCombos']:
                        add_category_option_combo(coc, cat_uids)

                organisationUnitGroups_uids += get_hardcoded_values_in_fields(metaobject, 'organisationUnitGroups',
                                                                              ['numerator', 'denominator'])
                # We don't expect to find any more OUG references at this point, so we can add the filter already
                if len(organisationUnitGroups_uids) > 0:
                    # Make list of UIDs unique
                    organisationUnitGroups_uids = list(dict.fromkeys(organisationUnitGroups_uids))
                    metadata_filters["organisationUnitGroups"] = "id:in:[" + ','.join(organisationUnitGroups_uids) + "]"

                # Scan for indicatorTypes
                if package_type_or_uid != "GEN":
                    indicatorTypes_uids = json_extract_nested_ids(metaobject, 'indicatorType')
                    metadata_filters["indicatorTypes"] = "id:in:[" + ','.join(indicatorTypes_uids) + "]"

                # Update the filters
                legendSets_uids += json_extract_nested_ids(metaobject, 'legendSets')

                if package_type_or_uid == 'DSH' or args.only_dashboards:
                    # Add [CONFIG] to the name and replace numerator and denominator expressions with -1
                    for indicator in metaobject:
                        if 'name' in indicator:
                            indicator['name'] = "[CONFIG] " + indicator['name']
                        if 'numerator' and 'denominator' in indicator:
                            indicator['numerator'] = -1
                            indicator['denominator'] = -1

            elif metadata_type == 'indicatorGroups':
                # If we have find one or more indicator groups based on prefix, use those to get
                # the indicators
                # Get indicator uids
                indicatorGroups_uids = json_extract(metaobject, 'id')
                indicator_uids = json_extract_nested_ids(metaobject, 'indicators')
                metadata_filters["indicators"] = "id:in:[" + ','.join(indicator_uids) + "]"
                # Check if there is an indicatorGroupSet
                for indGroup in metaobject:
                    if 'indicatorGroupSet' in indGroup:
                        indicatorGroupSets_uids.append(indGroup['indicatorGroupSet']['id'])
                metadata_filters["indicatorGroupSets"] = "id:in:[" + ','.join(indicatorGroupSets_uids) + "]"
            elif metadata_type == 'indicatorTypes':
                # Update legendSets filter (especially important for AGG and GEN packages)
                metadata_filters["legendSets"] = "id:in:[" + ','.join(legendSets_uids) + "]"
            elif metadata_type == 'dataElementGroups':
                dataElements_in_package = json_extract_nested_ids(metaobject, 'dataElements')
                metadata_filters["dataElements"] = "id:in:[" + ','.join(dataElements_in_package) + "]"
                dataElementsGroups_uids = json_extract(metaobject, 'id')
            elif metadata_type == 'options':
                # Get the option UIDs to validate option Groups and remove undesired options
                options_uids = json_extract(metaobject, 'id')
            elif metadata_type == "optionGroups":
                legendSets_uids += json_extract_nested_ids(metaobject, 'legendSets')
                # At this point, we have analysed all elements where legendSets can be referenced, so update that
                # filter too
                metadata_filters["legendSets"] = "id:in:[" + ','.join(legendSets_uids) + "]"
            elif metadata_type == "predictors":
                # For predictors we have
                # the expression: similar to indicators, may contain PG I{}, TEA A{}, constant C{}, DE + COC #{.}
                # contrary to other cases, the DEs used in Pred are going to be added to the final group of DEs
                # to include in the program. In other words, this variable is not used for check/validation
                # the field outputCombo which references a COC
                # the field output which references a DE
                dataElements_uids['PRED'] += get_hardcoded_values_in_fields(metaobject, 'dataElements_ind',
                                                                            'generator.expression')
                dataElements_uids['PRED'] += json_extract_nested_ids(metaobject, 'output')
                # Remove duplicates from the list
                dataElements_uids['PRED'] = list(dict.fromkeys(dataElements_uids['PRED']))
                # Used for validation
                if package_type_or_uid in ['TRK', 'EVT']:
                    programIndicators_uids['PRED'] += get_hardcoded_values_in_fields(metaobject, 'programIndicators',
                                                                                     'generator.expression')
                hardcoded_cocs = get_hardcoded_values_in_fields(metaobject, 'categoryOptionCombos',
                                                                'generator.expression')
                for coc in hardcoded_cocs:
                    if coc not in cat_uids['categoryOptionCombos']:
                        add_category_option_combo(coc, cat_uids)
            elif metadata_type == "predictorGroups":
                # Get predictor uids
                predictor_uids = json_extract_nested_ids(metaobject, 'predictors')
                metadata_filters["predictors"] = "id:in:[" + ','.join(predictor_uids) + "]"
                predictorGroups_uids = json_extract(metaobject, 'id')

            elif metadata_type == 'validationRuleGroups':
                # Find validation rule groups based on prefix
                # And then use those to find the validation rules
                validationRules_uids = json_extract_nested_ids(metaobject, 'validationRules')
                metadata_filters["validationRules"] = "id:in:[" + ','.join(validationRules_uids) + "]"
                metadata_filters["validationNotificationTemplates"] = "validationRules.id:in:[" + ','.join(
                    validationRules_uids) + "]"
                validationRuleGroups_uids = json_extract(metaobject, 'id')
            elif metadata_type == 'validationRules':
                # Analyze hardcoded expressions
                dataElements_uids['VR'] = get_hardcoded_values_in_fields(metaobject, 'dataElements_ind',
                                                                         ['leftSide.expression',
                                                                          'rightSide.expression'])

                hardcoded_cocs = get_hardcoded_values_in_fields(metaobject, 'categoryOptionCombos',
                                                                ['leftSide.expression', 'rightSide.expression'])
                for coc in hardcoded_cocs:
                    if coc not in cat_uids['categoryOptionCombos']:
                        add_category_option_combo(coc, cat_uids)
            elif metadata_type == "categoryOptions":
                if package_type_or_uid != 'GEN':
                    metadata_filters["categoryOptionGroups"] = "categoryOptions.id:in:[" + ','.join(cat_uids['categoryOptions']) + "]"
            elif metadata_type == "categoryOptionGroups":
                # For the GEN package, the groups are going to give us the categoryOptions
                if package_type_or_uid == 'GEN':
                    cat_uids['categoryOptions'] = json_extract_nested_ids(metaobject, 'categoryOptions')
                    # There should be just one group
                    cat_uids['categoryOptionGroups'] = json_extract(metaobject, 'id')
                    metadata_filters["categoryOptions"] = "id:in:[" + ','.join(cat_uids['categoryOptions']) + "]"
                else:
                    cat_uids['categoryOptionGroups'] = json_extract(metaobject, 'id')
                    metadata_filters["categoryOptionGroupSets"] = "categoryOptionGroups.id:in:[" + ','.join(
                        cat_uids['categoryOptionGroups']) + "]"
            elif metadata_type == "organisationUnitGroups":
                metadata_filters["organisationUnitGroupSets"] = "organisationUnitGroups.id:in:[" + ','.join(
                    organisationUnitGroups_uids) + "]"

        # Release log handlers
        handlers = logger.handlers[:]
        for handler in handlers:
            handler.close()
            logger.removeHandler(handler)

        if total_errors != 0:
            return None

        # Write metadata_object
        # last updated for the program will be the most recent date when any of the metadata was changed
        df_report_lastUpdated.sort_values(by=['last_updated'], ascending=False, inplace=True)
        # The element on top should contain the lastUpdated date
        last_time_program_was_updated = df_report_lastUpdated.iloc[0]['last_updated'][0:19].replace("-", "").replace(
            ":", "")

        # Update package label with time
        if 'package' in metadata:
            metadata['package']["lastUpdated"] = last_time_program_was_updated
        with open(name_label + '.json', 'w',
                  encoding='utf8') as file:
            file.write(json.dumps(metadata, indent=4, sort_keys=True, ensure_ascii=False))
        file.close()

        # Order and group by metadata type getting counts
        df_report_lastUpdated.sort_values(by=['metadata_type']) \
            .to_csv(package_type + '_' + package_prefix + '_metadata_summary.csv', index=None, header=True)
        # Use #.groupby(['metadata_type']).size().reset_index(name='counts') \  to get the counts

        # for debug - and potential use in pipeline
        print(name_label + '.json')

    return name_label + '.json'


if __name__ == "__main__":
    package_file = main()
    # if the number of errors > 0, exit with code -1
    if package_file is None:
        sys.exit(1)

