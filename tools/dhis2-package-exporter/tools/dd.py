from dhis2 import logger
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from faker import Faker
import calendar
from random import randrange, random, choice, uniform, seed, choices, randint, shuffle
from scipy.stats import expon
import re
import uuid
import numpy
from pandas import isnull


program_orgunits = list()
program_teas = list()
program_des = list()
optionSetDict = dict()

# def initialize(program_orgunits, program_teas, program_des, optionSetDict):
#     program_orgunits = api_source.get('organisationUnits',
#                                       params={"paging": "false",
#                                               "filter": "id:in:[" + ','.join(orgunits_uid) + "]",
#                                               "fields": "id,name,level"}).json()['organisationUnits']

def get_exp_random_dates_from_date_to_today(start_date, k):
    # start_date is in the form datetime.strptime('', '%Y-%m-%d')
    # k = Number of date to return

    def diff_month(d1, d2):
        return abs((d1.year - d2.year) * 12 + d1.month - d2.month)

    def get_random_date(start_date, end_date, shift):
        lower_date = start_date + relativedelta(months=+shift)
        upper_date = lower_date.replace(day=calendar.monthrange(lower_date.year, lower_date.month)[1])
        if upper_date > end_date:
            upper_date = end_date
        # print(lower_date.strftime('%Y-%m-%d'))
        # print(upper_date.strftime('%Y-%m-%d'))
        return lower_date + timedelta(
            # Get a random amount of seconds between `start` and `end`
            seconds=randint(0, int((upper_date - lower_date).total_seconds())),
        )

    end_date = datetime.today()

    # Number of months included from start_date to the current date
    number_of_months = diff_month(start_date, end_date)
    # Get a simple list with the numbers for each month (0 = month in start_date, 1 = month start date + 1, etc...
    month_numbers = list(range(0, (number_of_months + 1)))
    # Get the exponential weights to be used
    weights = expon.rvs(scale=0.1, loc=0, size=(number_of_months + 1))
    weights.sort()
    # Choose months randomly
    chosen_months = choices(population=month_numbers, weights=weights, k=k)
    # The variable to return is a list
    random_dates = list()
    # Loop through every month selected (defined by first_date of that month, last_date of that month) and find
    # a random day
    for m in chosen_months:
        random_dates.append((get_random_date(start_date, end_date, m)))

    return random_dates


def isInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def isFloat(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def isTimeFormat(input):
    try:
        datetime.strptime(input, '%H:%M')
        return True
    except ValueError:
        return False


def isDateFormat(input):
    try:
        datetime.strptime(input, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def choices_with_ratio(values, ratios, k):
    # values -> list of values to use. It can be just a simple value or an interval delimited with :
    # ratios -> list of ratios to use. Must have same length as ratios
    # k -> Number of values to generate
    # Make sure ratio is not Nan or empty string
    ratios = [x if not isnull(x) and x != "" else float(0) for x in ratios]
    rationed_number = [int(round(x * k)) for x in ratios]
    # The total number of values which will be generated applying the ratios and rounding the result
    total_generated = sum(rationed_number)
    if len(ratios) > k or total_generated > (k + k/2):
        logger.warning('The number of values to generate is too small for the high amount of ratios provided')
    if total_generated != k:
        # Find the ratios to correct
        # The idea is that if we have generated less than the total we will randomly increase the elements
        # having the highest ratio (to get more of what we should have more). Otherwise we will decrease
        # the elements with lowest ratio (to get less of what we should have less)
        if total_generated < k:
            ratios_to_correct = max(ratios)
        else:
            ratios_to_correct = min(ratios)
            if ratios_to_correct == float(0):
                #Remove them from ratios
                tmp_ratios = [ratios[i] for i in range(len(ratios)) if ratios[i] != ratios_to_correct]
                ratios_to_correct = min(tmp_ratios)
        # Index returns the first occurrence
        # highest_ratio_index = ratios.index(highest_ratio)
        # Find all occurrences
        indices = [i for i in range(len(ratios)) if ratios[i] == ratios_to_correct]
        number_of_iterations = 0
        while total_generated != k:
            if total_generated < k:
                # Add 1 to element with highest ratio
                rationed_number[choice(indices)] +=1
            elif total_generated > k:
                # Subtract 1 to element with highest ratio
                choosen_random_index = choice(indices)
                if rationed_number[choosen_random_index] > 0:
                    rationed_number[choosen_random_index] -=1
                else:
                    # Take it out from ratios and recalculate
                    ratios[choosen_random_index] = 0.0
                    minimum_ratio_not_zero = 1.0
                    indices = list()
                    for r in ratios:
                        if r < minimum_ratio_not_zero and r != 0.0:
                            minimum_ratio_not_zero = r
                    indices = [i for i in range(len(ratios)) if ratios[i] == minimum_ratio_not_zero]

            total_generated = sum(rationed_number)
            number_of_iterations +=1

            # We should not spend here too much time, otherwise it is worth resetting the indexes

            # if number_of_iterations == 25:
            #     indices = [i for i in range(len(ratios)) if ratios[i] <= (ratios_to_correct+0.1)]
            #     number_of_iterations = 0
    # Create list of values to return
    choices = list()
    if ':' not in values[0]:
        for i in range(0,len(values)):
            choices.extend([values[i]] * rationed_number[i])
    else:
        for i in range(0, len(values)):
            min_max_values = str(values[i]).split(":")
            if len(min_max_values) == 2:
                if isInt(min_max_values[0]) and isInt(min_max_values[1]):
                    min_value = int(min_max_values[0])
                    max_value = int(min_max_values[1])
                    if min_value < max_value:
                        choices.extend(numpy.random.randint(min_value, max_value, rationed_number[i]))
                    else:
                        logger.error('min value ' + str(min_value) + ' is greater than max value ' + str(max_value))
                elif isFloat(min_max_values[0]) and isFloat(min_max_values[1]):
                    min_value = float(min_max_values[0])
                    max_value = float(min_max_values[1])
                    if min_value < max_value:
                        choices.extend(numpy.random.uniform(min_value, max_value, rationed_number[i]))
                    else:
                        logger.error('min value ' + str(min_value) + ' is greater than max value ' + str(max_value))
                elif isDateFormat(min_max_values[0]) and (isDateFormat(min_max_values[1]) or min_max_values[1] == 'today'):
                    min_date = datetime.strptime(min_max_values[0], '%Y-%m-%d').date()
                    if min_max_values[1] == 'today':
                        max_date = date.today()
                    else:
                        max_date = datetime.strptime(min_max_values[1], '%Y-%m-%d').date()
                    if min_date < max_date:
                        days_between_dates = (max_date - min_date).days
                        random_days = numpy.random.randint(0, days_between_dates, rationed_number[i])
                        # For the moment, return date type
                        choices.extend(list(map(lambda x: (min_date + timedelta(days=int(x))), random_days)))
                    else:
                        logger.error('min date ' + min_max_values[0] + ' is greater than max date ' + min_max_values[1])
                else:
                    logger.error('Could not recognize value type for ' + min_max_values)

    shuffle(choices)

    return choices


def validate_value(value_type, value, optionSet = list()):
    # FILE_RESOURCE
    # ORGANISATION_UNIT
    # IMAGE
    # COORDINATE
    global program_orgunits

    correct = False

    if len(optionSet) > 0: # It is an option
        if value in optionSet:
            correct = True
    elif value_type == 'AGE': # Either an age in years/months/days or a date-of-birth (YYY-MM-DD)
        #if value.isnumeric() and 0 <= int(value) <= 120:
        if isDateFormat(value):
            correct = True
        # todo: check for years/months/days
    elif value_type == 'TEXT': # Text (length of text up to 50,000 characters)
        if len(value) <= 50000:
            correct = True
    elif value_type == 'LONG_TEXT': # Always true
        correct = True
    elif value_type == 'INTEGER_ZERO_OR_POSITIVE':
        if value.isnumeric() and 0 <= int(value):
            correct = True
            value = str(int(value)) # Cast float
    elif value_type == 'INTEGER_NEGATIVE':
        if value.isnumeric() and 0 > int(value):
            correct = True
            value = str(int(value))  # Cast float
    elif value_type == 'INTEGER_POSITIVE':
        if value.isnumeric() and 0 < int(value):
            correct = True
            value = str(int(value))  # Cast float
    elif value_type == 'INTEGER':
        if value.isnumeric():
            correct = True
            value = str(int(value))  # Cast float
    elif value_type == 'NUMBER':
        if value.isnumeric():
            correct = True
    elif value_type == 'DATE':
        if isDateFormat(value):
            correct = True
    elif value_type == 'TRUE_ONLY':
        value = value.lower()
        if value == 'true':
            correct = True
    elif value_type == 'BOOLEAN':
        value = value.lower()
        if value in ['true', 'false']:
            correct = True
        if value in ['yes', 'no']:
            correct = True
    elif value_type == 'TIME':
        if isTimeFormat(value):
            correct = True
    elif value_type == 'PERCENTAGE': # Any decimal value between 0 and 100
        if value.isnumeric() and 0 <= int(value) <= 100:
            correct = True
    elif value_type == 'UNIT_INTERVAL': # Any decimal value between 0 and 1
        if value.isnumeric() and 0 <= int(value) <= 1:
            correct = True
    elif value_type == 'ORGANISATION_UNIT':
        correct = False
        for ou in program_orgunits:
            if value == ou['id']:
                correct = True
    elif value_type == 'PHONE_NUMBER':
        chars = set('0123456789+ ')
        if any((c in chars) for c in value):
            correct = True
    else:
        logger.info('Warning, type ' + value_type + ' not supported')

    return correct, value


def create_dummy_value(uid, gender='M'):

    def findWholeWord(w):
        return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search

    global program_teas
    global program_des
    if uid == '':
        elem_type = 'enrollmentDate'
        element = dict()
    elif uid in program_teas:
        elem_type = 'tea'
        element = program_teas[uid]
    elif uid in program_des:
        elem_type = 'de'
        element = program_des[uid]
    else:
        elem_type = 'eventDate'
        element = dict()

    faker = Faker()
    Faker.seed()
    value = None
    min_value = -50#dummy_data_params['min_value']
    max_value = 50#dummy_data_params['max_value']
    # If it is not a DE or TEA, it is a enrollmentDate or eventDate, so we initialize to this value
    value_type = 'DATE'
    name = ""
    if elem_type in ['tea', 'de']:
        value_type = element['valueType']
        name = element['name']
    global optionSetDict
    global program_orgunits


    # Define some min / max values for teas
    if elem_type == 'tea':
        if findWholeWord('weight')(name):
            if findWholeWord('birth')(name):
                min_value = 500
                max_value = 5000
            else: # in kg
                min_value = 5.0
                max_value = 150.0

    if 'optionSet' in element:
        optionSet = element['optionSet']['id']
        if optionSet not in optionSetDict:
            options = api_source.get('options', params={"paging": "false",
                                                        "order": "sortOrder:asc",
                                                        "fields": "id,code",
                                                        "filter": "optionSet.id:eq:" + optionSet}).json()[
                'options']
            optionSetDict[optionSet] = json_extract(options, 'code')
        value = choice(optionSetDict[optionSet])

        if elem_type == 'tea' and (findWholeWord('sex')(name) or findWholeWord('gender')(name)):
            # It is an optionSet for sex/gender
            # Male, M, MALE
            # Female, F, FEMALE
            # Transgender, TG
            # Other, OTHER
            # Unknown, UNKNOWN
            if len(optionSetDict[optionSet]) > 2: # More genders than male/female
                #Introduce other with low probability
                if randrange(0, 1000) < 50:
                    gender = 'O'

            for option in optionSetDict[optionSet]:
                if gender == 'M' and option.lower() in ['male', 'm']:
                    value = option
                elif gender == 'F' and option.lower() in ['female', 'f']:
                    value = option
                elif gender == 'O' and option.lower() in ['other', 'unknown']:
                    value = option

    elif value_type == "BOOLEAN":
        value = choice(['true', 'false'])

    elif value_type == "TRUE_ONLY":
        # If present, it should be True, although if the user has unchecked it, it will be false
        value = choice(['true', None])

    elif value_type == "DATE":
        min_value = date(year=2015, month=1, day=1)
        max_value = datetime.today()
        value = faker.date_between(start_date=min_value, end_date=max_value).strftime("%Y-%m-%d")

    elif value_type == "TIME":
        value = faker.time()[0:5]  # To get HH:MM and remove SS

    elif value_type in ["TEXT", "LONG_TEXT"]:
        # Default behavior for
        value = faker.text()[0:100]
        # teas use TEXT for many standard person attributes
        if elem_type == 'tea':
            name_to_check = name.replace(" ", "").lower()
            if 'name' in name_to_check:
                if any(word in name_to_check for word in ['given', 'first']):
                    if gender == 'M':
                        value = faker.first_name_male()
                    elif gender == 'F':
                        value = faker.first_name_female()
                    elif gender == 'O':
                        value = faker.first_name()
                elif any(word in name_to_check for word in ['family', 'last']):
                    value = faker.last_name()
                else:
                    value = faker.name()
            elif findWholeWord('id')(name):
                value = 'ID-' + str(uuid.uuid4().fields[-1])[:7]
            elif findWholeWord('number')(name):
                value = 'N-' + str(uuid.uuid4().fields[-1])[:7]
            elif findWholeWord('code')(name):
                value = 'Code' + str(uuid.uuid4().fields[-1])[:4]
            elif 'address' in name_to_check:
                value = faker.address()
            elif any(word in name_to_check for word in ['job', 'employment', 'occupation']):
                value = faker.job()
            elif any(word in name_to_check for word in ['sex', 'gender']):
                value = choice(['MALE', 'FEMALE'])
        #     else:
        #         value = faker.text()[0:100]
        # else: # For data elements
        #     value = faker.text()[0:100]

    elif value_type == 'AGE':
        # age_range = choice(['child', 'adolescent', 'adult', 'retired'])
        age_ranges = choice([[1,5*365], [5*365,15*365], [15*365,65*365], [65*365,100*365]])
        today = date.today()

        days = randrange(age_ranges[0], age_ranges[1])
        value = (today - timedelta(days=days)).strftime("%Y-%m-%d")

    elif value_type == "INTEGER_POSITIVE":
        min_value = 1
        value = randrange(min_value, max_value)

    elif value_type == "INTEGER_ZERO_OR_POSITIVE":
        min_value = 0
        value = randrange(min_value, max_value)

    elif value_type == "INTEGER_NEGATIVE":
        max_value = -1
        value = randrange(min_value, max_value)

    elif value_type == "INTEGER":
        value = randrange(min_value, max_value)

    elif value_type == "NUMBER":
        value = round(uniform(min_value, max_value), 2)

    elif value_type == 'PERCENTAGE': # Any decimal value between 0 and 100
        value = round(uniform(0, 100), 2)

    elif value_type == 'UNIT_INTERVAL': # Any decimal value between 0 and 1
        value = round(uniform(0, 1), 2)

    elif value_type == 'ORGANISATION_UNIT':
        random_ou = choice(program_orgunits)
        value = random_ou['id']

    elif value_type == 'PHONE_NUMBER':
        value = faker.phone_number()
        strs, replacements = value, {"-": " ", "(": "", ")": "", "x": "", "(": "", ".": " "}
        value = "".join([replacements.get(c, c) for c in strs])
    else:
        logger.info('Warning, type ' + value_type + ' not supported')

    return value

def create_dummy_attributes(tei):
    new_attributes = list()
    if len(tei['attributes']) > 0:
        gender = choice(['M','F'])
        for tea in tei['attributes']:
            tea_uid = tea['attribute']
            new_attributes.append({'attribute':tea_uid, 'value':create_dummy_value(tea_uid, gender)})

    logger.info(json.dumps(new_attributes, indent=4))  # , sort_keys=True))

