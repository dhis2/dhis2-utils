import csv
from pprint import pprint

import requests
import json
from requests.auth import HTTPBasicAuth
from dotenv import dotenv_values

config = dotenv_values(".env")


base_url = config['DHIS2_BASE_URL']
username = config['DHIS2_USERNAME']
password = config['DHIS2_PASSWORD']
filename = config['DHIS2_USERS_FILENAME']

auth = HTTPBasicAuth(username, password)

with open(filename, newline='', encoding='utf-8') as csvfile:
    reader = list(csv.DictReader(csvfile, delimiter=';'))

# generate unique IDs for users
def generate_ids(count):
    try:
        req = requests.get(base_url+'/api/system/id.json?limit={0}'.format(count),
                           auth=auth)
        data = req.json()
        return data['codes']
    except:
        return []

# fetch UI Locales available in instance
def get_locales():
    try:
        req = requests.get(base_url+'/api/locales/ui.json',
                           auth=auth)
        data = req.json()
        return data
    except:
        return []


def get_users_for_group(group_id):
    try:
        req = requests.get(base_url + '/api/userGroups/{0}.json'.format(group_id),
                           auth=auth)
        data = req.json()
        return data['users']
    except Exception as e:
        print('Could not fetch users for group id {0}'.format(group_id))
        return ''

# fetch resources
def get_resource(name, key):
    try:
        req = requests.get(base_url + '/api/{0}.json?paging=false'.format(name),
                           auth=auth)
        data = req.json()
        resources = data[key]
        return resources
    except Exception as e:
        print('Could not fetch resource {0}'.format(name))
        return []


def create_users(payload):
    try:
        req = requests.post(base_url + '/api/metadata',
                            json=payload, auth=auth)
        print(req.json())
    except Exception as e:
        print(e)

# fetch all user roles 
def get_user_roles():
    return get_resource('userRoles', 'userRoles')

# fetch all org units
def get_organisation_units():
    return get_resource('organisationUnits', 'organisationUnits')

# fetch all user groups
def get_user_groups():
    return get_resource('userGroups', 'userGroups')


def get_resource_id(value, resources):
    # First check for exact ID match
    for resource in resources:
        if resource['id'] == value:
            return value
    for resource in resources:
        if resource['displayName'] == value:
            return resource['id']
    print(f"⚠️ Could not find resource match for '{value}'")
    return None


def get_locales_with_usernames(entries):
    system_locales = get_locales()
    print(system_locales)
    locales_and_username = []
    for row in entries:
        if row['locale'] != '':
            locales_and_username.append({
                "username": row['username'],
                "locale": list(filter(lambda x: x['locale'] == row['locale'], system_locales))[0]['locale']
            })
    return locales_and_username


# print(get_locales_with_usernames(reader))

# call to update user settings for users with locales given
def update_user_locales(entries):
    for element in entries:
        try:
            username = element['username']
            value = element['locale']
            # print('/api/userSettings/keyUiLocale?user={username}&value={value}'.format(
            # username=username, value=value))
            req = requests.post(base_url + '/api/userSettings/keyUiLocale?user={username}&value={value}'.format(
                username=username, value=value),
                auth=auth)
            print(req.json())

        except Exception as e:
            print(e)

# prepare userGroups payload
def create_user_groups(user_group_combos):
    try:
        group_ids_list = []
        for i in user_group_combos:
            for k, v in i.items():
                if k == "groupId":
                    for x in v:
                        group_ids_list.append(x)
        group_ids = set(group_ids_list)

        user_groups = []

        for group_id in group_ids:
            group_combos = list(
                filter(lambda x: group_id in x['groupId'], user_group_combos))
            id_index = 0
            if group_id in group_combos[0]['groupId']:
                id_index = group_combos[0]['groupId'].index(group_id)
            # print(id_index)

            user_ids_in_memory = [combo["userId"] for combo in group_combos]
            mapped_user_ids_in_memory = list(map(
                lambda x: {"id": x}, user_ids_in_memory))
            users = users = get_users_for_group(
                group_id) + mapped_user_ids_in_memory
            user_group = {
                "name": list(filter(lambda x: group_id in x['groupId'], user_group_combos))[0]["groupName"][id_index],
                "id": group_id,
                "users": users
            }
            user_groups.append(user_group)
        return user_groups
    except Exception as e:
        print('Exception in create user groups {0}'.format(e))
        return []

# prepare users payload
def create_user_list(entries):
    organisation_units = get_organisation_units()
    user_groups = get_user_groups()
    user_roles = get_user_roles()

    total_users = sum(1 for r in reader)
    user_ids = generate_ids(total_users)

    users = []
    user_group_combos = []

    for index, row in enumerate(entries):
        user_id = user_ids[index]
        user_roles_split = row['userRoles'].split(", ")
        oucapture_split = row['organisationUnits'].split(", ")
        ououtput_split = row['dataViewOrganisationUnits'].split(", ")
        user_groups_split = row['userGroups'].split(", ")
        user = {
            "id": user_id,
            "firstName": row['firstName'],
            "surname": row['surname'],
            "userCredentials": {
                "username": row['username'],
                "password": row['password'],
                "userRoles": list(map(lambda x: {"id": get_resource_id(
                    x, user_roles)}, user_roles_split))
            },
            "organisationUnits": list(map(lambda x: {"id": get_resource_id(
                x, organisation_units)}, oucapture_split)),
            "dataViewOrganisationUnits": list(map(lambda x: {"id": get_resource_id(
                x, organisation_units)}, ououtput_split))
        }

        user_group_combo = {
            "userId": user_id,
            "groupName": user_groups_split,
            "groupId": list(map(lambda x: get_resource_id(x, user_groups), user_groups_split)),
        }

        user_group_combos.append(user_group_combo)
        users.append(user)

    return users, user_group_combos


if __name__ == '__main__':

    print('Script running ...')
    users, combos = create_user_list(reader)
    user_groups = create_user_groups(combos)
    user_locales = get_locales_with_usernames(reader)
    payload = {
        "users": users,
        "userGroups": user_groups
    }
    pprint(payload)
    # print(user_locales)
    print('Importing users and updating usergroups...')
    create_users(payload)
    print("Updating user locales...")
    update_user_locales(user_locales)
