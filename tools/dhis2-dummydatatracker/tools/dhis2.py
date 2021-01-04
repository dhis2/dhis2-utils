from dhis2 import RequestException, logger
import json
import time
import re


def post_to_server(api, jsonObject, apiObject='metadata', strategy='CREATE_AND_UPDATE'):
    try:
        response = api.post(apiObject, params={'mergeMode': 'REPLACE', 'importStrategy': strategy},
                                   json=jsonObject)

    except RequestException as e:
        # Print errors returned from DHIS2
        logger.error("metadata update failed with error " + str(e))
        pass
    else:
        if response is None:
            logger.error("Error in response from server")
            return
        text = json.loads(response.text)
        # print(text)
        if text['status'] == 'ERROR':
            logger.error("Import failed!!!!\n" + json.dumps(text['typeReports'], indent=4, sort_keys=True))
            return False
        # errorCode = errorReport['errorCode']
        else:
            if apiObject == 'metadata':
                logger.info("metadata imported " + text['status'] + " " + json.dumps(text['stats']))
            else:
                # logger.info("data imported " + text['status'] + " " + json.dumps(text['importCount']))
                logger.info("Data imported\n" + json.dumps(text, indent=4, sort_keys=True))
                if text['status'] == 'WARNING': logger.warning(text)
            return True

# def isDHIS2UID(input):
#     pattern = re.compile(r'^[0-9a-zA-Z]{11}$')
#     if pattern.match(input):
#         return True
#     else:
#         return False


def post_chunked_data(api_endpoint, data_list, json_key, chunk_max_size):
    number_elems = len(data_list)
    if number_elems <= chunk_max_size:
        post_to_server(api_endpoint, {json_key: data_list}, json_key)
    chunk = dict()
    if number_elems < chunk_max_size:
        chunk_max_size = number_elems
    count = 0
    for x in range(0, number_elems, chunk_max_size):
        chunk[json_key] = data_list[x:(
            (x + chunk_max_size) if number_elems > (x + chunk_max_size) else number_elems)]
        count += 1

        retries = 0
        while retries <= 5:
            try:
                response = api_endpoint.post(json_key,
                                         params={'mergeMode': 'REPLACE', 'strategy': 'CREATE_AND_UPDATE'}, json=chunk)

            except RequestException as e:
                logger.error(str(e))
                time.sleep(3)
                retries += 1
            else:
                # Print success message
                text = json.loads(response.text)
                if 'status' in text and text['status'] == 'ERROR':
                    errorReport = text['typeReports'][0]['objectReports'][0]['errorReports'][0]
                    logger.error(errorReport)
                    errorCode = errorReport['errorCode']
                else:
                    if 'response' in text:
                        for key in ['importSummaries', 'importOptions', 'responseType']:
                            if key in text:
                                text.pop(key, None)
                        logger.info(json.dumps(text['response'], indent=4, sort_keys=True))
                    logger.info("Operation successful: chunk " + str(count) + " of " + str(json_key) + " created/updated")
                break


def find_ou_children_at_level(api_endpoint, ou_parent_uid, ou_children_level):
    params = {
        'fields': 'id,level,name',
        'filter': 'path:like:'+ou_parent_uid,
        'paging': 'false'
    }
    org_units = api_endpoint.get('organisationUnits', params=params).json()['organisationUnits']
    ou_children_uid_list = list()
    for ou in org_units:
        if ou['level'] == ou_children_level:
            ou_children_uid_list.append(ou['id'])
    return ou_children_uid_list

