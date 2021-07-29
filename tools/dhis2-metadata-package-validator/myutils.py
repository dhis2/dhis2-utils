
def get_name_by_type_and_uid(package, type, uid):
    return next((x for x in package[type] if x["id"] == uid), None)["name"]

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


def iterate_complex(d, func, level=1):
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, dict):
                #print(level, "-", k)
                iterate_complex(v, func, level+1)
            elif (isinstance(v, list)):
                #print(level, "-", k, ": list")
                func(k, v)
                for i in v:
                    iterate_complex(i, func, level+1)
            else:
                #print(level, "-", k,":",v)
                func(k, v)
    else:
        #print(level, "-", d)
        pass
