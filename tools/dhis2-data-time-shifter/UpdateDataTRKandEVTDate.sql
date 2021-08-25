CREATE OR REPLACE FUNCTION UpdateDataTRKandEVTDate (number_days integer) RETURNS boolean
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