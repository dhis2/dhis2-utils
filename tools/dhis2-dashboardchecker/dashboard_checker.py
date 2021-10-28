import json
from dhis2 import Api, RequestException, setup_logger, logger, is_valid_uid
import pandas as pd
from tools.json import json_extract
import argparse

log_file = "./dashboard_checker.log"
setup_logger(log_file)


def build_analytics_payload(json_object, verbose=False):

    def get_group_set_dimensions(json_object, key): # parent_key, child_key):
        parent_key = key+'Set'
        child_key = key+'s'
        for grp_set_dimension in json_object:
            grp_set_dimension_uid = grp_set_dimension[parent_key]['id']
            if child_key in grp_set_dimension:
                group_set_list = list()
                for group in grp_set_dimension[child_key]:
                    group_set_list.append(group['id'])
                dimensions[grp_set_dimension_uid] = group_set_list
            else:
                dimensions[grp_set_dimension_uid] = ""

    dimensions = dict()
    dimensions['ou'] = list()
    dimensions['pe'] = list()
    dimensions['dx'] = list()
    if 'organisationUnits' not in json_object or len(json_object['organisationUnits']) == 0:
        ou_global_selections = {'userOrganisationUnit':'USER_ORGUNIT',
                                'userOrganisationUnitChildren':'USER_ORGUNIT_CHILDREN',
                                'userOrganisationUnitGrandChildren':'USER_ORGUNIT_GRANDCHILDREN'}
        for ou_selection in ou_global_selections:
            if ou_selection in json_object and json_object[ou_selection] == True:
                dimensions['ou'].append(ou_global_selections[ou_selection])

        if 'organisationUnitLevels' in json_object and len(json_object['organisationUnitLevels']) > 0:
            ou_level_list = list()
            for org_unit_level in json_object['organisationUnitLevels']:
                ou_level_list.append('LEVEL-' + str(org_unit_level))
            if len(ou_level_list) > 0:
                dimensions['ou'] += ou_level_list

        if 'itemOrganisationUnitGroups' in json_object and len(json_object['itemOrganisationUnitGroups']) > 0:
            ou_group_list = list()
            for org_unit_group in json_object['itemOrganisationUnitGroups']:
                ou_group_list.append('OU_GROUP-' + str(org_unit_group['id']))
            if len(ou_group_list) > 0:
                dimensions['ou'] += ou_group_list
    else:
        dimensions['ou'] = json_extract(json_object['organisationUnits'], 'id')

    if 'periods' not in json_object or len(json_object['periods']) == 0:
        if 'relativePeriods' in json_object:
            pe_global_selections = {'thisDay': 'TODAY',
                                    'thisWeek': 'THIS_WEEK',
                                    'thisMonth': 'THIS_MONTH',
                                    'thisQuarter': 'THIS_QUARTER',
                                    'thisYear': 'THIS_YEAR',
                                    'lastDay': 'LAST_DAY',
                                    'lastWeek': 'LAST_WEEK',
                                    'lastMonth': 'LAST_MONTH',
                                    'lastQuarter': 'LAST_QUARTER',
                                    'lastYear': 'LAST_YEAR',
                                    'last30Days': 'LAST_30_DAYS',
                                    'last52Weeks': 'LAST_52_WEEKS',
                                    'last90Days': 'LAST_90_DAYS',
                                    'last60Days': 'LAST_60_DAYS',
                                    'last14Days': 'LAST_14_DAYS',
                                    'last2SixMonths': 'LAST_2_SIXMONTHS',
                                    'last12Months': 'LAST_12_MONTHS',
                                    'last4Weeks': 'LAST_4_WEEKS',
                                    'last3Months': 'LAST_3_MONTHS',
                                    'last5Years': 'LAST_5_YEARS',
                                    'last6Months': 'LAST_6_MONTHS',
                                    'last3Days': 'LAST_3_DAYS',
                                    'last7Days': 'LAST_7_DAYS',
                                    'last180Days': 'LAST_180_DAYS',
                                    'last12Weeks': 'LAST_12_WEEKS',
                                    'last4Quarters': 'LAST_4_QUARTERS',
                                    'weeksThisYear': 'WEEKS_THIS_YEAR',
                                    'yesterday': 'YESTERDAY',
                                    'quartersLastYear': 'QUARTERS_LAST_YEAR',
                                    'monthsThisYear': 'MONTHS_THIS_YEAR',
                                    'biMonthsThisYear': 'BI_MONTHS_THIS_YEAR',
                                    'last5FinancialYears': 'LAST_5_FINANCIAL_YEARS',
                                    'thisSixMonth': 'THIS_SIX_MONTH',
                                    'thisFinancialYear': 'THIS_FINANCIAL_YEAR',
                                    'last6BiMonths' : 'LAST_6_BI_MONTHS',
                                    'last4BiWeeks' : 'LAST_6_BI_WEEKS',
                                    'lastFinancialYear': 'LAST_FINANCIAL_YEAR',
                                    'lastBiWeek': 'LAST_BI_WEEK',
                                    'quartersThisYear': 'QUARTERS_THIS_YEAR',
                                    'monthsLastYear': 'MONTHS_LAST_YEAR',
                                    'thisBimonth': 'THIS_BI_MONTH',
                                    'lastBimonth': 'LAST_BI_MONTH',
                                    'lastSixMonth': 'LAST_SIX_MONTH',
                                    'thisBiWeek': 'THIS_BI_WEEK'}
            for relative_period in json_object['relativePeriods']:
                if relative_period in pe_global_selections:
                    if json_object['relativePeriods'][relative_period]:
                        dimensions['pe'].append(pe_global_selections[relative_period])
                else:
                    logger.error("Unknown relativePeriod " + relative_period)
                    exit(1)
            if len(dimensions['pe']) == 0 and 'periods' in json_object:
                dimensions['pe'] = json_extract(json_object['periods'], 'id')
        else:
            return {}
    else:
        dimensions['pe'] = json_extract(json_object['periods'], 'id')

    if len(dimensions['pe']) == 0 and 'startDate' in json_object and 'endDate' in json_object:
        del dimensions['pe']

    if 'dataDimensionItems' in json_object and len(json_object['dataDimensionItems']) > 0:
        data_dimension_keys = {'PROGRAM_INDICATOR': 'programIndicator',
                               'INDICATOR': 'indicator',
                               'DATA_ELEMENT': 'dataElement',
                               'REPORTING_RATE': 'reportingRate',
                               'PROGRAM_DATA_ELEMENT': 'programDataElement'}
        for data_dimension in json_object['dataDimensionItems']:
            # Sometimes there are empty dimensions
            if data_dimension != {}:
                if data_dimension['dataDimensionItemType'] in data_dimension_keys:
                    # Special case, it joins to UIDs with a .
                    if data_dimension['dataDimensionItemType'] == 'PROGRAM_DATA_ELEMENT':
                        UID1 = data_dimension[data_dimension_keys[data_dimension['dataDimensionItemType']]]['program']['id']
                        UID2 = data_dimension[data_dimension_keys[data_dimension['dataDimensionItemType']]]['dataElement']['id']
                        dimensions['dx'].append(UID1 + '.' + UID2)
                    else:
                        data_dimension_uid = data_dimension[data_dimension_keys[data_dimension['dataDimensionItemType']]]['id']
                        if data_dimension['dataDimensionItemType'] == 'REPORTING_RATE':
                            # For reporting rates, we need to add the keyword to the id
                            dimensions['dx'].append(data_dimension_uid + '.REPORTING_RATE')
                        else:
                            dimensions['dx'].append(data_dimension_uid)
                else:
                    logger.error('Unrecognized data dimension type ' + data_dimension['dataDimensionItemType'])
                    exit(1)

    dataElementDimension_filters = dict()
    if 'dataElementDimensions' in json_object and len(json_object['dataElementDimensions']) > 0:
        for data_element_dimension in json_object['dataElementDimensions']:
            data_element_dimension_uid = data_element_dimension['dataElement']['id']
            if 'filter' in data_element_dimension:
                dimensions[data_element_dimension_uid] = data_element_dimension['filter']
            else:
                dimensions[data_element_dimension_uid] = ""

    if 'categoryOptionGroupSetDimensions' in json_object and len(json_object['categoryOptionGroupSetDimensions']) > 0:
        get_group_set_dimensions(json_object['categoryOptionGroupSetDimensions'], 'categoryOptionGroup')
    if 'organisationUnitGroupSetDimensions' in json_object and len(json_object['organisationUnitGroupSetDimensions']) > 0:
        get_group_set_dimensions(json_object['organisationUnitGroupSetDimensions'], 'organisationUnitGroup')
    if 'dataElementGroupSetDimensions' in json_object and len(json_object['dataElementGroupSetDimensions']) > 0:
        get_group_set_dimensions(json_object['dataElementGroupSetDimensions'], 'dataElementGroup')

    if 'categoryDimensions' in json_object and len(json_object['categoryDimensions']) > 0:
        for category_dimension in json_object['categoryDimensions']:
            category_dimension_uid = category_dimension['category']['id']
            category_options = list()
            for cat_options in category_dimension['categoryOptions']:
                category_options.append(cat_options['id'])
            dimensions[category_dimension_uid] = category_options

    # Build the payload
    payload = ""
    params = dict()
    payload += 'dimension='
    params['dimension'] = ""
    added_column_dimension = False
    if 'columns' in json_object:
        first_element = True
        for column in json_object['columns']:
            added_column_dimension = True
            if not first_element:
                payload += ','
                params['dimension'] += ','
            else:
                first_element = False
            key = column['id']
            if key in dimensions:
                if isinstance(dimensions[key], list):
                    right_expression = ';'.join(dimensions[key])
                else:
                    right_expression = dimensions[key]
                payload += key + ':' + right_expression
                params['dimension'] += key + ':' + right_expression
            else:
                if key == 'pe' and 'startDate' in json_object and 'endDate' in json_object:
                    payload += "&startDate=" + json_object['startDate'] + "&endDate=" + json_object['endDate']
                    params['startDate'] = json_object['startDate']
                    params['endDate'] = json_object['endDate']
                else:
                    logger.error(json_object['id'] + ': Dimension ' + key + ' is missing')
                    # exit(1)
    else:
        logger.error('columns missing')
        exit(1)

    # A very specific and strange case for maps
    # empty columns but styleDataItem is present. In that case, it gets added to the dimension
    if 'columns' in json_object and len(json_object['columns']) == 0 and 'styleDataItem' in json_object:
        payload += json_object['styleDataItem']['id']
        params['dimension'] += json_object['styleDataItem']['id']
        if 'rows' in json_object and len(json_object['rows']) > 0:
            payload += ','
            params['dimension'] += ','

    if 'rows' in json_object:
        if len(json_object['rows']) > 0:
            # If we have already added some stuff, separate it with a comma
            if added_column_dimension:
                payload += ','
                params['dimension'] += ','
            first_element = True
            for row in json_object['rows']:
                if not first_element:
                    payload += ','
                    params['dimension'] += ','
                else:
                    first_element = False
                key = row['id']
                if key in dimensions:
                    payload += key + ':' + ';'.join(dimensions[key])
                    params['dimension'] += key + ':' + ';'.join(dimensions[key])
                else:
                    if key == 'pe' and 'startDate' in json_object and 'endDate' in json_object:
                        payload += "&startDate=" + json_object['startDate'] + "&endDate=" + json_object['endDate']
                        params['startDate'] = json_object['startDate']
                        params['endDate'] = json_object['endDate']
                    else:
                        logger.error(json_object['id'] + ': Dimension ' + key + ' is missing')
                        # exit(1)
    else:
        logger.error('rows missing')
        exit(1)

    if 'filters' in json_object:
        if len(json_object['filters']) > 0:
            payload += '&filter='
            params['filter'] = ""
            first_element = True
            for filter in json_object['filters']:
                if not first_element:
                    payload += ','
                    params['filter'] += ','
                else:
                    first_element = False
                key = filter['id']
                if key in dimensions:
                    payload += key + ':' + ';'.join(dimensions[key])
                    params['filter'] += key + ':' + ';'.join(dimensions[key])
                else:
                    if key == 'pe' and 'startDate' in json_object and 'endDate' in json_object:
                        payload += "&startDate=" + json_object['startDate'] + "&endDate=" + json_object['endDate']
                        params['startDate'] = json_object['startDate']
                        params['endDate'] = json_object['endDate']
                    else:
                        logger.error(json_object['id'] + ': Dimension ' + key + ' is missing')
                        # exit(1)
    else:
        logger.error('filters missing')
        exit(1)

    if 'programStage' in json_object:
        payload += '&stage' + ':' + json_object['programStage']['id']
        params['stage'] = json_object['programStage']['id']


    # Important, to get the data
    payload += "&skipData=false"
    params['skipData'] = 'false'

    if verbose:
        logger.info(payload)

    return params


def main():

    my_parser = argparse.ArgumentParser(description='dashboard_checker')
    my_parser.add_argument('-i', '--instance', action="store", dest="instance", type=str,
                           help='URL of the instance to process')
    my_parser.add_argument('-df', '--dashboard_filter', action="store", dest="dashboard_filter", type=str,
                           help='Either a prefix or a list of comma separated UIDs')
    my_parser.add_argument('--no_data_warning', dest='no_data_warning', action='store_true')
    my_parser.add_argument('--omit-no_data_warning', dest='no_data_warning', action='store_false')
    my_parser.add_argument('-v', '--verbose', dest='verbose', action='store_true')
    my_parser.set_defaults(no_data_warning=True)
    my_parser.set_defaults(verbose=False)
    args = my_parser.parse_args()

    if args.instance is not None:
        instances = [{'name': args.instance.split('/')[-1].replace(':','_'),
                     'url': args.instance}]
    else:
        instances = [
           #{'name':'newdemos', 'url':'https://who-demos.dhis2.org/newdemos', 'SQL_view_TRK':'xfemQFHUTUV', 'SQL_view_AGG':'lg8lFbDMw2Z'}
           #{'name':'tracker_dev', 'url': 'https://who-dev.dhis2.org/tracker_dev', 'SQL_view_TRK': 'xfemQFHUTUV', 'SQL_view_AGG': 'lg8lFbDMw2Z'}
            {'name': 'covid-19', 'url': 'https://demos.dhis2.org/covid-19', 'SQL_view_TRK': 'xfemQFHUTUV',
             'SQL_view_AGG': 'lg8lFbDMw2Z'}
        ]

    credentials_file = './auth.json'

    df = pd.DataFrame({}, columns=['dashboard_name', 'type', 'uid', 'name', 'issue', 'api_link', 'app_link'])

    errors_found = 0

    for instance in instances:
        try:
            f = open(credentials_file)
        except IOError:
            print("Please provide file auth.json with credentials for DHIS2 server")
            exit(1)
        else:
            with open(credentials_file, 'r') as json_file:
                credentials = json.load(json_file)
            api_source = Api(instance['url'], credentials['dhis']['username'], credentials['dhis']['password'])

        # Get dashboards
        params = {
            "fields": "*",
            "paging": "false"
        }
        if args.dashboard_filter is not None:
            item_list = args.dashboard_filter.split(',')
            if len(item_list) == 1 and not is_valid_uid(item_list[0]):
                params["filter"] = "name:$like:" + args.dashboard_filter
            # Let's consider it as a list of uids
            else:
                # Validate the list
                for item in item_list:
                    if not is_valid_uid(item):
                        logger.error("UID " + item + " is not a valid DHIS2 UID")
                        exit(1)
                params["filter"] = "id:in:[" + args.dashboard_filter + "]"

        dashboards = api_source.get('dashboards', params=params).json()['dashboards']

        dashboard_item_with_issues_row = dict()
        for dashboard in dashboards:
            logger.info('Processing dashboard ' + dashboard['name'])
            dashboard_item_with_issues_row['dashboard_name'] = dashboard['name']
            if '2.33' not in api_source.version:
                dashboard_items = ['visualization', 'eventReport', 'eventChart', 'map']
            else:
                dashboard_items = ['chart', 'reportTable', 'eventReport', 'eventChart', 'map']
            for dashboardItem in dashboard['dashboardItems']:
                # The dashboard item could be of type TEXT, for example
                # in this case there is nothing to do
                dashboard_item_type_found = False
                for dashboard_item in dashboard_items:
                    if dashboard_item in dashboardItem:
                        dashboard_item_type_found = True
                        dashboard_item_with_issues_row['issue'] = ""
                        dashboard_item_with_issues_row['type'] = dashboard_item
                        dashboard_item_with_issues_row['uid'] = dashboardItem[dashboard_item]['id']
                        dashboard_item_with_issues_row['name'] = ""
                        if args.verbose:
                            logger.info('Trying ' + dashboard_item + ' ' + dashboardItem[dashboard_item]['id'])
                        try:
                            api_endpoint = dashboard_item + 's/' + dashboardItem[dashboard_item]['id']
                            dashboard_item_with_issues_row['api_link'] = instance['url'] + '/api/' +  api_endpoint
                            item = api_source.get(api_endpoint, params={"fields":"*"}).json()
                        except RequestException as e:
                            logger.error(dashboard_item + ' ' + dashboardItem[dashboard_item]['id'] + " BROKEN with error " + str(e))
                            dashboard_item_with_issues_row['issue'] = str(e)
                            errors_found += 1
                        else:
                            dashboard_item_with_issues_row['name'] = item['name']
                            if dashboard_item in ['eventReport', 'eventChart']:
                                continue
                            # Try to get the data
                            try:
                                if dashboard_item == 'map':
                                    for map_view in item['mapViews']:
                                        params = build_analytics_payload(map_view, args.verbose)
                                        if params != {}:
                                            if 'layer' in map_view and map_view['layer'] == 'event' and 'program' in map_view:
                                                data = api_source.get('analytics/events/query/' + map_view['program']['id'], params=params).json()
                                            else:
                                                data = api_source.get('analytics', params=params).json()
                                else:
                                    data = api_source.get('analytics', params=build_analytics_payload(item, args.verbose)).json()
                            except RequestException as e:
                                logger.error(dashboard_item + ' ' + dashboardItem[dashboard_item]['id'] + " data cannot be retrieved with error " + str(e))
                                dashboard_item_with_issues_row['issue'] = str(e)
                                errors_found += 1
                            else:
                                # print(data['rows'])
                                if args.no_data_warning and ('rows' not in data or len(data['rows']) == 0):
                                    dashboard_item_with_issues_row['issue'] = 'NO DATA'
                                    logger.warning(dashboardItem[dashboard_item]['id'] + ': NO DATA!!!')

                            #exit(0)

                if dashboard_item_type_found and dashboard_item_with_issues_row['issue'] != "":
                    if dashboard_item_with_issues_row['type'] == 'visualization':
                        dashboard_item_with_issues_row['app_link'] = instance['url'] + \
                                                                     '/dhis-web-data-visualizer/index.html#/' + \
                                                                     dashboard_item_with_issues_row['uid']
                    elif dashboard_item_with_issues_row['type'] == 'map':
                        dashboard_item_with_issues_row['app_link'] = instance['url'] + \
                                                                     '/dhis-web-maps/index.html'
                    elif dashboard_item_with_issues_row['type'] == 'eventReport':
                        dashboard_item_with_issues_row['app_link'] = instance['url'] + \
                                                                     'dhis-web-event-reports/index.html?id=' + \
                                                                     dashboard_item_with_issues_row['uid']
                    elif dashboard_item_with_issues_row['type'] == 'eventChart':
                        dashboard_item_with_issues_row['app_link'] = instance['url'] + \
                                                                     '/dhis-web-event-visualizer/index.html?id=' + \
                                                                     dashboard_item_with_issues_row['uid']
                    df = df.append(dashboard_item_with_issues_row, ignore_index=True)

    export_csv = df.to_csv(instance['name'] + '.csv', index=None, header=True)

    # Release log handlers
    handlers = logger.handlers[:]
    for handler in handlers:
        handler.close()
        logger.removeHandler(handler)

    return errors_found


if __name__ == '__main__':
    num_error = main()
    # if the number of errors > 0, exit with code -1
    if num_error > 0:
        exit(1)
