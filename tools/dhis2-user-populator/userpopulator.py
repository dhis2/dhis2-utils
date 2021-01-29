import csv
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

reader = tuple(csv.DictReader(open(filename)))

# generate unique IDs for users
def generate_ids(count):
    try:
        req = requests.get(base_url+'/api/system/id.json?limit={0}'.format(count),
                           auth=auth)
        data = req.json()
        return data['codes']
    except:
        return []

# fetch UI Locales available an instance
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


def get_user_roles():
    return get_resource('userRoles', 'userRoles')


def get_organisation_units():
    return get_resource('organisationUnits', 'organisationUnits')


def get_user_groups():
    return get_resource('userGroups', 'userGroups')


def get_resource_id(name, resources):
    for resource in resources:
        if resource['displayName'] == name:
            return resource['id']


def get_locales_with_usernames(entries):
    system_locales = get_locales()
    print(system_locales)
    locales_and_username = []
    for row in entries:
        if row['locale'] != '':
            locales_and_username.append({
                "username": row['username'],
                "locale": list(filter(lambda x: x['name'] == row['locale'], system_locales))[0]['locale']
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

# create userGroup payload
def create_user_groups(user_group_combos):
    try:
        group_ids = set([group["groupId"] for group in user_group_combos])

        user_groups = []

        for group_id in group_ids:
            group_combos = filter(
                lambda x: x["groupId"] == group_id, user_group_combos)
            user_ids_in_memory = [combo["userId"] for combo in group_combos]
            mapped_user_ids_in_memory = list(map(
                lambda x: {"id": x}, user_ids_in_memory))
            users = get_users_for_group(group_id) + mapped_user_ids_in_memory

            user_group = {
                "name": list(filter(lambda x: x["groupId"] == group_id, user_group_combos))[0]["groupName"],
                "id": group_id,
                "users": users
            }
            user_groups.append(user_group)
        return user_groups
    except Exception as e:
        print('Exception in create user groups {0}'.format(e))
        return []

# create users payload
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
        user = {
            "id": user_id,
            "firstName": row['firstName'],
            "surname": row['surname'],
            "userCredentials": {
                "username": row['username'],
                "password": row['password'],
                "userRoles": [
                    {
                        "id": get_resource_id(row['userRoles'], user_roles)
                    }
                ]
            },
            "organisationUnits": [
                {
                    "id": get_resource_id(row['organisationUnits'], organisation_units)
                }
            ],
            "dataViewOrganisationUnits": [
                {
                    "id": get_resource_id(row['dataViewOrganisationUnits'], organisation_units)
                }
            ]
        }

        user_group_combo = {
            "userId": user_id,
            "groupName": row["userGroups"],
            "groupId": get_resource_id(row['userGroups'], user_groups),
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
    # print(payload)
    # print(user_locales)
    print('Importing users and updating usergroups...')
    create_users(payload)
    print("Updating user locales...")
    update_user_locales(user_locales)
