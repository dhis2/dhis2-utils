# dhis2-data-time-shifter

Move your Tracker / Event / Agg data in time by X days

## For Tracker/Event data

```sql
CREATE FUNCTION UpdateDataTRKandEVTDate (number_days integer) RETURNS boolean
    LANGUAGE plpgsql
AS
$$
DECLARE
    TABLE_RECORD RECORD;
BEGIN

     -- Only required for Tracker: Update enrollment date
     UPDATE programinstance
     SET enrollmentdate = enrollmentdate::TIMESTAMP + (number_days::TEXT || ' DAY')::INTERVAL,
         lastupdated = NOW();

     -- Only required for Tracker: Update TEA values for enrollments
     UPDATE trackedentityattributevalue teav
     SET value = DATE(value::TIMESTAMP + (number_days::TEXT || ' DAY')::INTERVAL)
     FROM trackedentityattribute tea
     WHERE tea.trackedentityattributeid = teav.trackedentityattributeid AND
     tea.valuetype = 'DATE';

     -- Update event dates
     UPDATE programstageinstance
     SET executiondate = executiondate::TIMESTAMP + (number_days::TEXT || ' DAY')::INTERVAL,
         duedate = duedate::TIMESTAMP + (number_days::TEXT || ' DAY')::INTERVAL,
         completeddate = completeddate::TIMESTAMP + (number_days::TEXT || ' DAY')::INTERVAL,
         lastupdated = NOW();
     
    -- Update DE values for events
    FOR TABLE_RECORD IN
        select psi.programstageinstanceid,
           ('{'||js.key||',value}')::TEXT[] as path,
           ('"'||TEXT(DATE(to_timestamp(replace(js_value.value::TEXT, '"', ''), 'YYYY-MM-DD') + (number_days::TEXT || ' DAY')::INTERVAL))||'"')::jsonb as value
        from programstageinstance psi, jsonb_each(eventdatavalues::jsonb) as js, jsonb_each(js.value) as js_value
        where js.key IN (SELECT uid FROM dataelement WHERE valuetype = 'DATE') AND js_value.key = 'value'
    LOOP
        UPDATE programstageinstance psi 
        SET eventdatavalues = jsonb_set(eventdatavalues, TABLE_RECORD.path, TABLE_RECORD.value)
        WHERE psi.programstageinstanceid = TABLE_RECORD.programstageinstanceid;
    END LOOP;

    RETURN TRUE;
END
$$;
```

This function shiftes all dates of enrollment and event data by number_days in the future

Execution example:
```sql
SELECT UpdateDataTRKandEVTDate(1);
```

Some key things here:
- This function changes the dates for enrollment and, for each event, the event date, due date and completed date. lastUpdated is updated accordingly to reflect this update.
- For trackedEntityAttributes and dataElement values, it updates all the data stored for a metadata of valueType = DATE. Nothing is done for the moment for DATETIME, but changing valuetype = 'DATE' to valuetype IN ('DATE', 'DATETIME') as well as the casting to DATE should be a goos starting point.
- eventdatavalues as stored as a jsonb object. For jsonb, there is a function called [jsonb_set](https://www.postgresql.org/docs/9.5/functions-json.html) which receives teh following parameters: target jsonb, path text[], new_value jsonb
The purpose of this query
```sql
        select psi.programstageinstanceid,
           ('{'||js.key||',value}')::TEXT[] as path,
           ('"'||TEXT(DATE(to_timestamp(replace(js_value.value::TEXT, '"', ''), 'YYYY-MM-DD') + (number_days::TEXT || ' DAY')::INTERVAL))||'"')::jsonb as value
        from programstageinstance psi, jsonb_each(eventdatavalues::jsonb) as js, jsonb_each(js.value) as js_value
        where js.key IN (SELECT uid FROM dataelement WHERE valuetype = 'DATE') AND js_value.key = 'value'
```
is to produce effectively the parameters required to update each dataelementvalue of type DATE for every programstageinstance.
The target will simply be eventdatavalues jsonb object.
The path will look something like this: '{DE_UID,value}', i.e. "I want to update the value for key = DE_UID"
The new_value is the current DATE value for this DE + (number_days::TEXT || ' DAY')::INTERVAL

After the table with all updates is built, an update for each row runs performing the required updates.

Please be aware that for a size of 100K events in the DB, this query may take 5mins.

Also, remember to run analytics to see the changes in your dashboards :)


## For Aggregate data

This function receives the period_type to consider and it shiftes the data in datavalues table (aggregate data) to the next period available.

Execution example:
```sql
SELECT UpdateDataAGGDate('Daily');
```

```sql
CREATE FUNCTION UpdateDataAGGDate (period_type text) RETURNS boolean
    LANGUAGE plpgsql
AS
$$
DECLARE
BEGIN

    WITH tbl_shift_date as 
    (
        SELECT 
        dataelementid,
        sourceid,
        categoryoptioncomboid,
        attributeoptioncomboid,
        value,
        dv.periodid as old_periodid,
        pt.name as frequency,
        pp.periodtypeid, pp.startdate,
        CASE WHEN pp.name = 'Daily' THEN DATE(pp.startdate + INTERVAL '1 DAY')
             WHEN pp.name = 'Weekly' THEN DATE(pp.startdate + INTERVAL '7 DAY')
             WHEN pp.name = 'Monthly' THEN DATE(date_trunc('month', pp.startdate + INTERVAL '1 MONTH'))
             WHEN pp.name = 'Quarterly' THEN DATE(date_trunc('quarter', pp.startdate + INTERVAL '3 MONTH'))
             WHEN pp.name = 'Yearly' THEN DATE(date_trunc('year', pp.startdate + INTERVAL '1 YEAR'))
        END as new_date
        FROM datavalue dv 
        LEFT JOIN period pp on dv.periodid = pp.periodid
        LEFT JOIN periodtype pt on pp.periodtypeid = pt.periodtypeid
        ORDER BY pp.startdate DESC
    )
    SELECT dv.dataelementid, dv.sourceid, dv.categoryoptioncomboid, dv.attributeoptioncomboid, dv.value, tbl_shift_date.old_periodid, tbl_shift_date.startdate, new_period.periodid, new_period.startdate
    FROM tbl_shift_date
    INNER JOIN datavalue dv ON
        dv.dataelementid = tbl_shift_date.dataelementid AND
        dv.sourceid = tbl_shift_date.sourceid AND
        dv.categoryoptioncomboid = tbl_shift_date.categoryoptioncomboid AND
        dv.attributeoptioncomboid = tbl_shift_date.attributeoptioncomboid AND
        dv.value = tbl_shift_date.value AND -- Not part of the unique key
        dv.periodid = tbl_shift_date.old_periodid
    INNER JOIN period new_period on tbl_shift_date.periodtypeid = new_period.periodtypeid AND new_period.startdate = tbl_shift_date.new_date
    WHERE
        tbl_shift_date.frequency = period_type;

    RETURN TRUE;
END
$$;
```

Some key things here:
- For the moment Daily, Weekly, Monthly, Quarterly and Yearly are supported.
If you want to add support for an aditional period type, you simply need to add a new WHEN statement in the CASE, e.g.:
```sql
WHEN pp.name = 'WeeklyThursday' THEN ...
```

- In order to be able to change the current period to the next one, the table period must have that period already created. Let's say you run a select for period type Monthly on the table and this is what you get:
```
 periodid | startdate  |  enddate
----------+------------+------------
    78204 | 2021-01-01 | 2021-01-31
    78205 | 2021-02-01 | 2021-02-28
    78206 | 2021-03-01 | 2021-03-31
    78207 | 2021-04-01 | 2021-04-30
    78208 | 2021-05-01 | 2021-05-31
    80342 | 2020-01-01 | 2020-01-31
    80343 | 2020-02-01 | 2020-02-29
    80344 | 2020-03-01 | 2020-03-31
    80345 | 2020-04-01 | 2020-04-30
    80346 | 2020-05-01 | 2020-05-31
    80347 | 2020-06-01 | 2020-06-30
    80348 | 2020-07-01 | 2020-07-31
    80349 | 2020-08-01 | 2020-08-31
    80350 | 2020-09-01 | 2020-09-30
    80351 | 2020-10-01 | 2020-10-31
    80352 | 2020-11-01 | 2020-11-30
    80353 | 2020-12-01 | 2020-12-31
```

As you can see, the last period available is May 2021 (2021-05-01 to 2021-05-31).
If you attempt shifting the data to the next month by calling UpdateDataAGGDate('Monthly'), the data for May will fail to be updated.
In order to create those entries, you need to either enter some data in a monthly dataSet for the periods you are missing, or import that data.

To simplify this, there is a python script in this folder called: populate_period_table.py

You will need to make sure you have the package dhis2 installed:
```bash
pip install dhis2
```

Create auth.json file containing the credentials of the default server to use. The script relies on a username 'robot' with SuperUser role to have an account in the server.

```json
{
  "dhis": {
    "baseurl": "https://who-dev.dhis2.org/tracker_dev",
    "username": "robot",
    "password": "TOPSECRET"
  }
}
```

Call the script as follows:
```bash
python populate_period_table.py period_type start_date end_date instance_url
```
period_type can be Daily, Weekly, Monthly, Quarterly OR Yearly

start_date in the format YYYY-MM-DD

end_date in the format YYYY-MM-DD

instance_url if you want to run it in an instance different from the one specified in auth.json (user credentials are the ones given in auth.json)


For example:
```bash
python populate_period_table.py Monthly 2021-01-01 2021-12-31 https://who-demos.dhis2.org/covid-19
```

When we run the same SELECT on the period table, we can see that the missing monthly periods for 2021 have been created:
```
 periodid | startdate  |  enddate
----------+------------+------------
   109465 | 2021-06-01 | 2021-06-30
   109466 | 2021-07-01 | 2021-07-31
   109467 | 2021-08-01 | 2021-08-31
   109468 | 2021-09-01 | 2021-09-30
   109469 | 2021-10-01 | 2021-10-31
   109470 | 2021-11-01 | 2021-11-30
   109471 | 2021-12-01 | 2021-12-31
    78204 | 2021-01-01 | 2021-01-31
    78205 | 2021-02-01 | 2021-02-28
    78206 | 2021-03-01 | 2021-03-31
    78207 | 2021-04-01 | 2021-04-30
    78208 | 2021-05-01 | 2021-05-31
    80342 | 2020-01-01 | 2020-01-31
    80343 | 2020-02-01 | 2020-02-29
    80344 | 2020-03-01 | 2020-03-31
    80345 | 2020-04-01 | 2020-04-30
    80346 | 2020-05-01 | 2020-05-31
    80347 | 2020-06-01 | 2020-06-30
    80348 | 2020-07-01 | 2020-07-31
    80349 | 2020-08-01 | 2020-08-31
    80350 | 2020-09-01 | 2020-09-30
    80351 | 2020-10-01 | 2020-10-31
    80352 | 2020-11-01 | 2020-11-30
    80353 | 2020-12-01 | 2020-12-31
```


