def reindex(json_list, key):
    """
    Remove index based on key. Receives a list and returns a dict using key as index

    Args:
      json_list (list): list of dictionaries
      key (str): the key to use as dict key

    Returns:
        new_json (dict) the json dict indexed by key
    """
    new_json = dict()
    for elem in json_list:
        if key in elem:
            key_value = elem[key]
        else:
            print('Error ' + key + ' not found')
            return False
        # elem.pop(key)
        new_json[key_value] = elem
    return new_json


def extract_json_element_as_list(json_list, key):
    """
    Loops through a list of dict, and checks if key is present. If so, it is added to a new list

    Args:
      json_list (list): list of dictionaries
      key (str): the key to find

    Returns:
        result (list) the values of key in each of the dict composing the list
    """
    result = list()
    for json_dict in json_list:
        if key in json_dict:
            result.append(json_dict[key])
    return result


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


def remove_duplicates_by_id(metaobject):
    """
    Remove dupicate metadata objects in a list

    Args:
      metaobject (list): metadata object to clean

    Returns:
        metaobject (list) the json object without duplicates
    """
    # If it is not a list, return the same
    if not isinstance(metaobject, list):
        return metaobject
    else:
        unique_list_of_ids = list()
        new_metaobject = list()
        for obj in metaobject:
            if 'id' in obj:
                id = obj['id']
                if id not in unique_list_of_ids:
                    unique_list_of_ids.append(id)
                    new_metaobject.append(obj)

    return new_metaobject

