import json
import chardet
import sys
import pandas as pd
from datetime import datetime

# api_source = Api('https://test.performance.dhis2.org/2.34', 'admin', 'district')
#
# setup_logger()


def reindex(json_object, key):
    new_json = dict()
    for elem in json_object:
        key_value = elem[key]
        # elem.pop(key)
        new_json[key_value] = elem
    return new_json


def json_extract(obj, key):
    """Recursively fetch values from nested JSON."""
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


# Convert json to dictionary
def json_to_dict(obj):
    separator = '.'

    result_dict = dict()
    key = ""

    skip_keys = ['translations', 'lastUpdated', 'lastUpdatedBy', 'href', 'access', 'created', 'allItems',
                 'displayName', 'displayDescription', 'displayNumeratorDescription', 'displayDenominatorDescription',
                 'displayFormName', 'displayShortName']

    def scan(obj, result_dict, key):
        if key == "":
            s = ""
        else:
            s = separator
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k not in skip_keys:
                    if isinstance(v, (dict, list)):
                        scan(v, result_dict, key + s + k)
                    else:
                        final_key = key + s + k
                        if final_key not in result_dict:
                            result_dict[final_key] = v
                        else:
                            if isinstance(result_dict[final_key], list):
                                result_dict[final_key].append(v)
                            # convert into a list
                            else:
                                result_dict[final_key] = [result_dict[final_key], v]
                            # result_dict[final_key].sort()

        elif isinstance(obj, list):
            for item in obj:
                scan(item, result_dict, key)
        return result_dict

    values = scan(obj, result_dict, key)
    return values


def json_extract_nested_ids(obj, key):
    """Recursively fetch values from nested JSON."""
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == key:
                    if isinstance(v, list):
                        for item in v:
                            arr.append(item["id"]) if item["id"] not in arr else arr
                    else:
                        arr.append(v)
                elif isinstance(v, (dict, list)):
                    extract(v, arr, key)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    values = extract(obj, arr, key)
    return values


def append_row_element(metaobj, df, type, operation, update = []):
    cols_to_add = ['id', 'name', 'lastUpdated', 'lastUpdatedBy']
    values = dict()
    for col in cols_to_add:
        if col in metaobj:
            values[col] = metaobj[col]
        else:
            values[col] = ""
    if operation != 'UPDATE' and len(update) == 0:
        return df.append(
            {'metadata_type': type, 'uid': values['id'], 'name': values['name'], 'operation': operation,
             'update_operation': '', 'update_key': '', 'update_diff': '',
             'last_updated': values['lastUpdated'], 'updated_by': values['lastUpdatedBy']}
            , ignore_index=True)
    else:
        if len(update) > 0:
            first_row = True
            for upd in update:
                if first_row:
                    df = df.append(
                        {'metadata_type': type, 'uid': values['id'], 'name': values['name'], 'operation': operation,
                         'update_operation': upd['update_operation'], 'update_key': upd['update_key'], 'update_diff': upd['update_diff'],
                         'last_updated': values['lastUpdated'], 'updated_by': values['lastUpdatedBy']}
                        , ignore_index=True)
                else:
                    df = df.append(
                        {'metadata_type': '', 'uid': '', 'name': '', 'operation': '',
                         'update_operation': upd['update_operation'], 'update_key': upd['update_key'], 'update_diff': upd['update_diff'],
                         'last_updated': '', 'updated_by': ''}
                        , ignore_index=True)
                first_row = False
            return df


# Get element present in list2 but not in list1
def diff_list(list1, list2):
    result = []
    for elem in list2:
        if elem not in list1:
            result.append(elem)
    return result


if __name__ == '__main__':

    package_file1 = sys.argv[1]
    package_file2 = sys.argv[2]

    df = pd.DataFrame({}, columns=['metadata_type', 'operation', 'uid', 'name',
                                   'update_operation', 'update_key', 'update_diff', 'last_updated', 'updated_by'])

    delete_payload = dict()

    enc = chardet.detect(open(package_file1, 'rb').read())['encoding']
    with open(package_file1, 'r', encoding=enc) as json_file:
        metadata1 = json.load(json_file)
    with open(package_file2, 'r', encoding=enc) as json_file:
        metadata2 = json.load(json_file)

    ###### Check if new metadata types have been deleted/created
    keys1 = list(metadata1.keys())
    keys2 = list(metadata2.keys())

    # Consolidate all keys into one list and order it alphabetically
    keys = list(dict.fromkeys(keys1 + keys2))
    keys.sort()
    for key in keys:
        # All elements have been removed
        if key in metadata1 and key not in metadata2:
            for element in metadata1[key]:
                df = append_row_element(element, df, key, 'DELETED')
        # All elements have been created
        elif key in metadata2 and key not in metadata1:
            for element in metadata2[key]:
                df = append_row_element(element, df, key, 'CREATED')
        # Look at individual elements
        else:
            ##### Check that a single metadata type and look for new/deleted/updated elements
            if isinstance(metadata1[key], list) and isinstance(metadata2[key], list):
                # Convert a list into a dictionary indexed by uid
                metaobj1 = reindex(metadata1[key], 'id')
                metaobj2 = reindex(metadata2[key], 'id')
                uids1 = list(metaobj1.keys())
                uids2 = list(metaobj2.keys())

                # Consolidate all keys into one list and order it alphabetically
                uids = list(dict.fromkeys(uids1 + uids2))
                uids.sort()

                for uid in uids:
                    if uid in metaobj1 and uid not in metaobj2:
                        df = append_row_element(metaobj1[uid], df, key, 'DELETED')
                        if key not in delete_payload:
                            delete_payload[key] = list()
                        delete_payload[key].append(metaobj1[uid])
                    # All elements have been created
                    elif uid in metaobj2 and uid not in metaobj1:
                        df = append_row_element(metaobj2[uid], df, key, 'CREATED')
                    # This element may have been updated
                    else:
                        #### Check for created/deleted/updated fields within same elements
                        # Try to use here the diff tool metaobj1[uid] VS metaobj2[uid]
                        dict1 = json_to_dict(metaobj1[uid])
                        dict2 = json_to_dict(metaobj2[uid])

                        k1 = list(dict1.keys())
                        k2 = list(dict2.keys())

                        # Consolidate all keys into one list and order it alphabetically
                        elem_keys = list(dict.fromkeys(k1 + k2))
                        elem_keys.sort()

                        update_list = []
                        for k in elem_keys:
                            if k in dict1 and k not in dict2:
                                if isinstance(dict1[k], list):
                                    #update_list.append("DELETED|" + k + " : " + 'list(' + str(len(dict1[k])) + ')')
                                    update_list.append({"update_operation":"DELETED",
                                                        "update_key": k + " : " + 'list(' + str(len(dict1[k])) + ')',
                                                        "update_diff": ""})
                                else:
                                    #update_list.append("DELETED|" + k + " : " + str(dict1[k]))
                                    update_list.append({"update_operation":"DELETED",
                                                        "update_key": k + " : " + str(dict1[k]),
                                                        "update_diff": ""})
                            # All elements have been created
                            elif k in dict2 and k not in dict1:
                                if isinstance(dict2[k], list):
                                    #update_list.append("CREATED|" + k + " : " + 'list(' + str(len(dict2[k])) + ')')
                                    update_list.append({"update_operation":"CREATED",
                                                        "update_key": k + " : " + 'list(' + str(len(dict2[k])) + ')',
                                                        "update_diff": ""})
                                else:
                                    #update_list.append("CREATED|" + k + " : " + str(dict2[k]))
                                    update_list.append({"update_operation":"CREATED",
                                                        "update_key": k + " : " + str(dict2[k]),
                                                        "update_diff": ""})
                            # This element may have been updated
                            else:
                                if isinstance(dict1[k], list) and isinstance(dict2[k], list):
                                    if dict1[k].sort() != dict2[k].sort():
                                        msg = ""
                                        # Get deleted elements in second list
                                        deleted = diff_list(dict2[k], dict1[k])
                                        if len(deleted) > 0:
                                            msg += "DEL: " + str(deleted)
                                        # Get added elements in second list
                                        added = diff_list(dict1[k], dict2[k])
                                        if len(added) > 0:
                                            if msg != "":
                                                msg += " "
                                            msg += "ADD: " + str(added)
                                        #update_list.append("UPDATED|" + k + "|" + msg)
                                        update_list.append({"update_operation": "UPDATED",
                                                            "update_key": k,
                                                            "update_diff": msg})

                                else:
                                    if dict1[k] != dict2[k]:
                                        #update_list.append("UPDATED|" + k + "|" + str(dict1[k]) + " -> " + str(dict2[k]))
                                        update_list.append({"update_operation": "UPDATED",
                                                            "update_key": k,
                                                            "update_diff": str(dict1[k]) + " -> " + str(dict2[k])})
                        if len(update_list) > 0:
                            df = append_row_element(metaobj2[uid], df, key, 'UPDATED', update_list)

            # It is most likely the PACKAGE label
            else:
                if metadata1[key] != metadata2[key]:
                    df = df.append(
                        {'metadata_type': key, 'uid': '', 'name': '', 'operation': 'UPDATED',
                         'update_operation': 'UPDATED', 'update_key': '',
                         'update_diff': str(metadata1[key]) + " -> " + str(metadata2[key]),
                         'last_updated': '', 'updated_by': ''}
                        , ignore_index=True)


    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("%d-%b-%Y_%H-%M-%S")
    export_csv = df.to_csv(r'./comparison_' + timestampStr + '.csv', index=None, header=True)

    if delete_payload != {}:
        with open('package_diff_delete.json', 'w', encoding='utf8') as file:
            file.write(json.dumps(delete_payload, indent=4, sort_keys=True, ensure_ascii=False))
        file.close()


