
-- SQL script for moving data from one year to the next.
-- Useful for updating demo databases with sample data.
-- (Write) Move startdate and enddate in period to next year
-- Change the year to reflect the current time. Periods are
-- moved one year at the time to avoid unique constraint violations.
------------------------------------------------------Part 1 move  all Data forward by one year ----------------------------------------------
DROP FUNCTION

IF EXISTS dhis2_timeshift_one_year_forward_core(update_event_dates BOOLEAN);
	CREATE
		OR replace FUNCTION dhis2_timeshift_one_year_forward_core (update_event_dates BOOLEAN DEFAULT FALSE)
	RETURNS VOID LANGUAGE plpgsql AS $$

DECLARE f record;

TABLE_RECORD record;

BEGIN
	--This part  is  a query to get the list of all years in the current DHIS2 instance, which have  data values  to be moved forward by one year
	FOR f IN

	SELECT DISTINCT date_part('year', startdate) AS years
	FROM period
	ORDER BY years DESC LOOP

	UPDATE period
	SET startdate = (startdate + interval '1 year')::DATE
		,enddate = (enddate + interval '1 year')::DATE
	WHERE date_part('year', startdate)::INT = f.years;
END

LOOP;

-- (Write) Move programstageinstance	
UPDATE programstageinstance
SET duedate = (duedate + interval '1 year')
	,executiondate = (executiondate + interval '1 year')
	,completeddate = (completeddate + interval '1 year');

-- (Write) Move programinstance to next year
UPDATE programinstance
SET incidentdate = (incidentdate + interval '1 year')
	,enrollmentdate = (enrollmentdate + interval '1 year')
	,enddate = (enddate + interval '1 year');

-- (Write) Move interpretations created / lastupdated to next year
UPDATE interpretation
SET created = (created + interval '1 year');

UPDATE interpretation
SET lastupdated = created;

-- (Write) Move favorite start/end dates to next year	
UPDATE mapview
SET startdate = (startdate + interval '1 year')
WHERE startdate IS NOT NULL;

UPDATE mapview
SET enddate = (enddate + interval '1 year')
WHERE enddate IS NOT NULL;

UPDATE eventreport
SET startdate = (startdate + interval '1 year')
WHERE startdate IS NOT NULL;

UPDATE eventreport
SET enddate = (enddate + interval '1 year')
WHERE enddate IS NOT NULL;

UPDATE eventchart
SET startdate = (startdate + interval '1 year')
WHERE startdate IS NOT NULL;

UPDATE eventchart
SET enddate = (enddate + interval '1 year')
WHERE enddate IS NOT NULL;

-- Only required for Tracker: Update TEA values for enrollments
UPDATE trackedentityattributevalue teav
SET value = to_char((value::DATE + interval '1 year'), 'YYYY-MM-dd')
WHERE trackedentityattributeid IN (
		SELECT trackedentityattributeid
		FROM trackedentityattribute
		WHERE valuetype IN (
				'DATE'
				,'DATETIME'
				)
		);

-- (Write) Move date event values to next year
UPDATE trackedentitydatavalueaudit
SET value = to_char((value::DATE + interval '1 year'), 'YYYY-MM-dd')
WHERE dataelementid IN (
		SELECT dataelementid
		FROM dataelement
		WHERE valuetype IN (
				'DATE'
				,'DATETIME'
				)
			AND domaintype = 'TRACKER'
		);

-- HAVING NAIVELY MOVED PERIOD DATES ONE YEAR FORWARD, WE NEED TO TWEAK THE DATES TO ALIGN PERIODS CORRECTLY
-- Deal with all of the start dates first, then adjust the end dates at the end.
-- Move the start day of all Weekly periods to Monday
UPDATE period
SET startdate = startdate + 1 - cast(abs(extract(isodow FROM startdate)) AS INT)
FROM periodtype
WHERE period.periodtypeid = periodtype.periodtypeid
	AND periodtype.name LIKE ('Weekly');

-- Move the start day of all WeeklyWednesday periods to Wednesday
UPDATE period
SET startdate = startdate + 3 - cast(abs(extract(isodow FROM startdate)) AS INT)
FROM periodtype
WHERE period.periodtypeid = periodtype.periodtypeid
	AND periodtype.name LIKE ('WeeklyWednesday');

-- Move the start day of all WeeklyThursday periods to Thursday
UPDATE period
SET startdate = startdate + 4 - cast(abs(extract(isodow FROM startdate)) AS INT)
FROM periodtype
WHERE period.periodtypeid = periodtype.periodtypeid
	AND periodtype.name LIKE ('WeeklyThursday');

-- Move the start day of all WeeklySaturday periods to Saturday
UPDATE period
SET startdate = startdate + 6 - cast(abs(extract(isodow FROM startdate)) AS INT)
FROM periodtype
WHERE period.periodtypeid = periodtype.periodtypeid
	AND periodtype.name LIKE ('WeeklySaturday');

-- Move the start day of all WeeklySunday periods to Sunday
UPDATE period
SET startdate = startdate + 7 - cast(abs(extract(isodow FROM startdate)) AS INT)
FROM periodtype
WHERE period.periodtypeid = periodtype.periodtypeid
	AND periodtype.name LIKE ('WeeklySunday');

-- Set all weeks to one week long :)
UPDATE period
SET enddate = to_char(startdate + interval '6 days', 'YYYY-MM-DD')::DATE
FROM periodtype
WHERE period.periodtypeid = periodtype.periodtypeid
	AND periodtype.name LIKE ('%Weekly%');

-- Ensure all months are correct length
-- Monthly
UPDATE period
SET enddate = (period.startdate + (interval '1 month') - (interval '1 day'))::DATE
FROM periodtype
WHERE period.periodtypeid = periodtype.periodtypeid
	AND periodtype.name LIKE ('Monthly');

-- BiMonthly
UPDATE period
SET enddate = (period.startdate + (interval '2 months') - (interval '1 day'))::DATE
FROM periodtype
WHERE period.periodtypeid = periodtype.periodtypeid
	AND periodtype.name LIKE ('BiMonthly');

-- SixMonthly
UPDATE period
SET enddate = (period.startdate + (interval '6 months') - (interval '1 day'))::DATE
FROM periodtype
WHERE period.periodtypeid = periodtype.periodtypeid
	AND periodtype.name LIKE ('SixMonthly%');
    
-- Update event dates if update_event_dates set to TRUE, the below part will take time 
IF update_event_dates THEN		
    FOR TABLE_RECORD IN SELECT
    psi.programstageinstanceid,
    ( '{' || js.KEY || ',value}' ) :: TEXT [] AS PATH,
    ('"'||TEXT(DATE(to_timestamp(replace(js_value.value::TEXT, '"', ''), 'YYYY-MM-DD')))||'"')::jsonb as old_date ,
    (
        '"' || TEXT ( DATE ( to_timestamp( REPLACE ( js_value.VALUE :: TEXT, '"', '' ), 'YYYY-MM-DD' ) + ( '1 year' ) :: INTERVAL ) ) || '"' 
    ) :: jsonb AS VALUE

    FROM
        programstageinstance psi,
        jsonb_each ( eventdatavalues :: jsonb ) AS js,
        jsonb_each ( js.VALUE ) AS js_value 
    WHERE
        js.KEY IN ( SELECT uid FROM dataelement WHERE valuetype = 'DATE' ) 
        AND js_value.KEY = 'value'

        LOOP
        UPDATE programstageinstance psi 
        SET eventdatavalues = jsonb_set ( eventdatavalues, TABLE_RECORD.PATH, TABLE_RECORD.VALUE ) 
    WHERE	psi.programstageinstanceid = TABLE_RECORD.programstageinstanceid;
    END LOOP;
END IF;	

	END;$$;

-- SQL script for moving data backward by one year
-- Useful for updating demo databases with sample data.

Drop function if EXISTS dhis2_timeshift_one_year_backward_core (update_event_dates BOOLEAN);
create or replace function dhis2_timeshift_one_year_backward_core (update_event_dates BOOLEAN DEFAULT FALSE) RETURNS VOID 
LANGUAGE plpgsql
  AS

$$

declare

    f record;
	TABLE_RECORD record;

begin
   
--This part  is  a query to get the list of all years in the current DHIS2 instance, which have  data values  to be moved backward by one year
FOR f IN select   DISTINCT date_part('year',startdate) as years from period
order by years asc

loop 
update period set
startdate = (startdate + interval '-1 year')::date,
enddate = (enddate + interval '-1 year')::date
where date_part('year', startdate)::int = f.years;
end loop;

-- (Write) Move programstageinstance	
update programstageinstance set
duedate = (duedate + interval '-1 year'),
executiondate = (executiondate + interval '-1 year'),
completeddate = (completeddate + interval '-1 year');

-- (Write) Move programinstance to next year
update programinstance set
incidentdate = (incidentdate + interval '-1 year'),
enrollmentdate = (enrollmentdate + interval '-1 year'),
enddate = (enddate + interval '-1 year');

-- (Write) Move interpretations created / lastupdated to next year
update interpretation set created = (created + interval '-1 year');
update interpretation set lastupdated = created;
-- (Write) Move favorite start/end dates to next year	
update mapview set startdate = (startdate + interval '-1 year') where startdate is not null;
update mapview set enddate = (enddate + interval '-1 year') where enddate is not null;

update eventreport set startdate = (startdate + interval '-1 year') where startdate is not null;
update eventreport set enddate = (enddate + interval '-1 year') where enddate is not null;

update eventchart set startdate = (startdate + interval '-1 year') where startdate is not null;
update eventchart set enddate = (enddate + interval '-1 year') where enddate is not null;

-- Only required for Tracker: Update TEA values for enrollments
  UPDATE trackedentityattributevalue teav
     SET value = to_char((value::date + interval '-1 year'), 'YYYY-MM-dd')
		 where trackedentityattributeid in (
  select trackedentityattributeid from trackedentityattribute where valuetype in ('DATE','DATETIME') 
);

-- (Write) Move date event values to next year
update trackedentitydatavalueaudit set value = to_char((value::date + interval '-1 year'), 'YYYY-MM-dd')
where dataelementid in (
  select dataelementid from dataelement where valuetype in ('DATE','DATETIME') and domaintype = 'TRACKER'
);


-- HAVING NAIVELY MOVED PERIOD DATES ONE YEAR FORWARD, WE NEED TO TWEAK THE DATES TO ALIGN PERIODS CORRECTLY

-- Deal with all of the start dates first, then adjust the end dates at the end.
-- Move the start day of all Weekly periods to Monday
UPDATE period
	SET startdate = startdate + 1 - cast(abs(extract(isodow from startdate)) as int)
	FROM periodtype
 	WHERE period.periodtypeid = periodtype.periodtypeid AND periodtype.name LIKE ('Weekly');
-- Move the start day of all WeeklyWednesday periods to Wednesday
UPDATE period
	SET startdate = startdate + 3 - cast(abs(extract(isodow from startdate)) as int)
	FROM periodtype
 	WHERE period.periodtypeid = periodtype.periodtypeid AND periodtype.name LIKE ('WeeklyWednesday');
-- Move the start day of all WeeklyThursday periods to Thursday
UPDATE period
	SET startdate = startdate + 4 - cast(abs(extract(isodow from startdate)) as int)
	FROM periodtype
 	WHERE period.periodtypeid = periodtype.periodtypeid AND periodtype.name LIKE ('WeeklyThursday');
-- Move the start day of all WeeklySaturday periods to Saturday
UPDATE period
	SET startdate = startdate + 6 - cast(abs(extract(isodow from startdate)) as int)
	FROM periodtype
 	WHERE period.periodtypeid = periodtype.periodtypeid AND periodtype.name LIKE ('WeeklySaturday');
-- Move the start day of all WeeklySunday periods to Sunday
UPDATE period
	SET startdate = startdate + 7 - cast(abs(extract(isodow from startdate)) as int)
	FROM periodtype
 	WHERE period.periodtypeid = periodtype.periodtypeid AND periodtype.name LIKE ('WeeklySunday');
-- Set all weeks to one week long :)
UPDATE period
	SET enddate = to_char(startdate + interval '6 days', 'YYYY-MM-DD')::date
	FROM periodtype
 	WHERE period.periodtypeid = periodtype.periodtypeid AND periodtype.name LIKE ('%Weekly%');
-- Ensure all months are correct length
-- Monthly
UPDATE period
	SET enddate = (period.startdate + (interval '1 month') - (interval '1 day'))::date
	FROM periodtype
 	WHERE period.periodtypeid = periodtype.periodtypeid AND periodtype.name LIKE ('Monthly');
-- BiMonthly
UPDATE period
	SET enddate = (period.startdate + (interval '2 months') - (interval '1 day'))::date
	FROM periodtype
 	WHERE period.periodtypeid = periodtype.periodtypeid AND periodtype.name LIKE ('BiMonthly');
-- SixMonthly
UPDATE period
	SET enddate = (period.startdate + (interval '6 months') - (interval '1 day'))::date
	FROM periodtype
 	WHERE period.periodtypeid = periodtype.periodtypeid AND periodtype.name LIKE ('SixMonthly%');
	
-- Update event dates if update_event_dates set to TRUE, the below part will take time 
IF update_event_dates THEN
	FOR TABLE_RECORD IN SELECT
	psi.programstageinstanceid,
	( '{' || js.KEY || ',value}' ) :: TEXT [] AS PATH,
	('"'||TEXT(DATE(to_timestamp(replace(js_value.value::TEXT, '"', ''), 'YYYY-MM-DD')))||'"')::jsonb as old_date ,
	(
		'"' || TEXT ( DATE ( to_timestamp( REPLACE ( js_value.VALUE :: TEXT, '"', '' ), 'YYYY-MM-DD' ) + ( '-1 year' ) :: INTERVAL ) ) || '"' 
	) :: jsonb AS VALUE
		
	FROM
		programstageinstance psi,
		jsonb_each ( eventdatavalues :: jsonb ) AS js,
		jsonb_each ( js.VALUE ) AS js_value 
	WHERE
		js.KEY IN ( SELECT uid FROM dataelement WHERE valuetype = 'DATE' ) 
		AND js_value.KEY = 'value'

		LOOP
		UPDATE programstageinstance psi 
		SET eventdatavalues = jsonb_set ( eventdatavalues, TABLE_RECORD.PATH, TABLE_RECORD.VALUE ) 
	WHERE	psi.programstageinstanceid = TABLE_RECORD.programstageinstanceid;
	END LOOP;	
END IF;	
	end;
$$;


--This part to call the  FUNCTION to move forward all DHIS2 data by one year
----------------------------------only call at the begining of each year if needed-------------------------------------
CREATE OR REPLACE FUNCTION dhis2_timeshift_one_year_forward()
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    -- Call the dhis2_timeshift_one_year_forward_core function
    PERFORM dhis2_timeshift_one_year_forward_core(TRUE);

END;
$$;

CREATE OR REPLACE FUNCTION dhis2_timeshift_one_year_forward_no_events()
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    -- Call the dhis2_timeshift_one_year_forward_core function
    PERFORM dhis2_timeshift_one_year_forward_core();

END;
$$;

--This part to call the  FUNCTION to move backward all DHIS2 data by one year
----------------------------------only call at the begining of each year if needed-------------------------------------
CREATE OR REPLACE FUNCTION dhis2_timeshift_one_year_backward()
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    -- Call the dhis2_timeshift_one_year_backward_core function
    PERFORM dhis2_timeshift_one_year_backward_core(TRUE);

END;
$$;

CREATE OR REPLACE FUNCTION dhis2_timeshift_one_year_backward_no_events()
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    -- Call the dhis2_timeshift_one_year_backward_core function
    PERFORM dhis2_timeshift_one_year_backward_core();

END;
$$;

	--------------------------------------------------------------------------------------------------------------------------------
	--generating  buffer periods from the future/current  year to be used as a buffering period 
	--the buffering periods will be the same periodId for the future/current year with an extra two digits from  the buffering year
	-- --------------------------------------------------------------------------------------------------------------------------
	DROP FUNCTION

	IF EXISTS dhis2_timeshift_generate_buffer_from_current_core();
		CREATE
			OR replace FUNCTION dhis2_timeshift_generate_buffer_from_current_core ()
		RETURNS TABLE (
				p_id BIGINT
				,p_type INT
				,p_start DATE
				,p_end DATE
				,p_old_startdate DATE
				,p_old_enddate DATE
				,p_name2 VARCHAR
				--	p_month_no int
				) LANGUAGE plpgsql AS $$

	DECLARE var_r record;

	var_r_r record;

	min_p_year INT;

	min_p_datavalue_year INT;

	rec record;

	BEGIN
		---this part of the query will return a minimum year which has data values 
		min_p_year := (
				SELECT date_part('year', min(pp.startdate)) - 1 AS bufferyear_no_p
				FROM period pp
				);

		min_p_datavalue_year := (
				SELECT date_part('year', min(pp.startdate)) - 1 AS bufferyear_no_pv
				FROM datavalue dv
				LEFT JOIN period pp ON dv.periodid = pp.periodid
				LEFT JOIN periodtype pt ON pp.periodtypeid = pt.periodtypeid
				);

		IF min_p_year != min_p_datavalue_year THEN raise notice 'empty peroid will be  deleted from peroid table';FOR
			rec IN

		SELECT periodid
		FROM period
		WHERE date_part('year', startdate) <= min_p_datavalue_year LOOP

		DELETE
		FROM period
		WHERE periodid = rec.periodid;

		raise notice 'peroidid deleted  (%)'
			,rec.periodid;
			-- return NEXT ; -- return current row of SELECT
	END

	LOOP;ELSE

	raise notice 'peroid for year   (%) will be populated'
		,min_p_datavalue_year;
END

IF ;FOR
	var_r IN (
			WITH temp_buffer_year AS (
					SELECT date_part('year', min(pp.startdate)) - 1 AS bufferyear_no
					FROM period pp
					)
				,current_year AS (
					SELECT pp.periodid AS pid
						,pp.startdate AS Sdate
						,pp.enddate AS Edate
						,pp.periodtypeid AS newperiodtypeid
						,pt.name AS periodType
						,pp.periodtypeid
						,pp.startdate
						,CONCAT (
							pp.periodid
							,pp.periodtypeid
							) AS newpid
					FROM period pp
					INNER JOIN periodtype pt ON pp.periodtypeid = pt.periodtypeid
					WHERE date_part('year', startDate) = date_part('year', now()) --NULLIF(future_year, 2025)
					ORDER BY pp.periodtypeid
						,pp.startdate
					)
				,
				---this part of the query will return a list of periods of the buffering year
				Buffer_peroid AS (
					SELECT sdate
						,Edate
						,int8(CONCAT (
								pid
								,right(cast(bufferyear_no AS TEXT), 2)
								)) AS new_buffer_Peroidid
						,newperiodtypeid AS new_buffer_periodtypeid
						,cast(CONCAT (
								cast(bufferyear_no AS TEXT)
								,right(cast(Sdate AS TEXT), 6)
								) AS DATE) AS newbfSdate
						,cast(CONCAT (
								cast(bufferyear_no AS TEXT)
								,right(cast(Edate AS TEXT), 6)
								) AS DATE) AS newbfEdate
						,periodType
					FROM temp_buffer_year
						,current_year
						---this part of the query will fix the start and end date of the periods in the buffering year
					)
				,new_Buffer_peroid AS (
					SELECT new_buffer_Peroidid
						,new_buffer_periodtypeid
						,Sdate
						,CASE 
							--WHEN periodType= 'Weekly' THEN newbfSdate + 1 - cast(abs(extract(isodow from newbfSdate)) as int)  
							WHEN periodType = 'WeeklyWednesday'
								THEN newbfSdate + 3 - cast(abs(extract(isodow FROM newbfSdate)) AS INT)
							WHEN periodType = 'WeeklyThursday'
								THEN newbfSdate + 4 - cast(abs(extract(isodow FROM newbfSdate)) AS INT)
							WHEN periodType = 'WeeklySaturday'
								THEN newbfSdate + 6 - cast(abs(extract(isodow FROM newbfSdate)) AS INT)
							WHEN periodType = 'WeeklySunday'
								THEN newbfSdate + 7 - cast(abs(extract(isodow FROM newbfSdate)) AS INT)
							WHEN periodType = 'Daily'
								THEN newbfSdate
							WHEN periodType = 'Monthly'
								THEN newbfSdate
							ELSE newbfSdate
							END AS new_startdate
						,CASE 
							WHEN periodType = '%Weekly%'
								THEN to_char(newbfSdate + interval '6 days', 'YYYY-MM-DD')::DATE
							WHEN periodType = 'Monthly'
								THEN (newbfSdate + (interval '1 month') - (interval '1 day'))::DATE
							WHEN periodType = 'BiMonthly'
								THEN (newbfSdate + (interval '2 months') - (interval '1 day'))::DATE
							WHEN periodType = 'SixMonthly%'
								THEN (newbfSdate + (interval '6 months') - (interval '1 day'))::DATE
							ELSE newbfEdate
							END AS new_enddate
						,Sdate AS startdate_old
						,Edate AS enddate_old
						,periodType AS ptname
					FROM Buffer_peroid
					)
			SELECT *
			FROM new_Buffer_peroid
			) LOOP p_id := var_r.new_buffer_Peroidid;

p_type := var_r.new_buffer_periodtypeid;

p_start := var_r.new_startdate;

p_end := var_r.new_enddate;

p_old_startdate := var_r.startdate_old;

p_old_enddate := var_r.enddate_old;

p_name2 := var_r.ptname;

--	p_month_no  := var_r.month_no;
RETURN NEXT;END

LOOP;END;$$;



---------------------------------------------- Move all future data to the buffer period-----------------
-- Move all future data to the buffer period , Using today date as a baseline
DROP FUNCTION

IF EXISTS dhis2_timeshift_move_future_to_buffer_core();
	CREATE FUNCTION dhis2_timeshift_move_future_to_buffer_core ()
	RETURNS boolean LANGUAGE plpgsql
	AS
	$$

	DECLARE

	BEGIN
		WITH buffer_year_peroid
		AS (
			SELECT left(cast(periodid AS TEXT), - 2)::BIGINT AS old_peroid
				,periodid
				,periodtypeid
				,startdate
				,enddate
				,date_part('year', startdate) AS buffer_year
			FROM period
			WHERE date_part('year', startdate) = (
					SELECT date_part('year', min(pp.startdate))
					FROM period pp
					)
			)
			,feature_year_peroid
		AS (
			SELECT periodid::BIGINT AS pp
				,periodtypeid
				,startdate
				,enddate
			FROM period
			WHERE date_part('year', startdate) = date_part('year', now())
			)
			,pre_update
		AS (
			SELECT old_peroid
				,bf_year.periodid AS new_peroid
				,f_year.startdate AS f_startdate
				,f_year.enddate AS f_enddate
				,bf_year.periodtypeid
				,pp
				,bf_year.startdate AS bf_startdate
				,bf_year.enddate AS bf_enddate
			FROM buffer_year_peroid bf_year
			JOIN feature_year_peroid f_year ON f_year.pp = bf_year.old_peroid
			)
			,dv2
		AS (
			SELECT dataelementid
				,sourceid
				,categoryoptioncomboid
				,attributeoptioncomboid
				,value
				,dv.periodid
			FROM datavalue dv
			INNER JOIN pre_update ON dv.periodid = pre_update.pp
			)
		UPDATE datavalue dv
		SET periodid = pre_update.new_peroid
		FROM pre_update
		INNER JOIN dv2 ON dv2.periodid = pre_update.old_peroid
		WHERE dv.periodid = pre_update.old_peroid
			AND pre_update.f_startdate >= now()::DATE
			AND dv2.dataelementid = dv.dataelementid
			AND dv2.sourceid = dv.sourceid
			AND dv2.categoryoptioncomboid = dv.categoryoptioncomboid
			AND dv2.attributeoptioncomboid = dv.attributeoptioncomboid
			AND dv2.value = dv.value;

		RETURN TRUE;
	END $$;

--  the following function wraps calls to the create and fill the buffer period 
CREATE OR REPLACE FUNCTION dhis2_timeshift_buffer_future_periods()
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    -- Run the function to delete empty periods in the buffering year to avoid duplicated period IDs
    PERFORM dhis2_timeshift_generate_buffer_from_current_core();

    -- Create all buffer periods
    INSERT INTO period
    SELECT p_id, p_type, p_start, p_end
    FROM dhis2_timeshift_generate_buffer_from_current_core();

	PERFORM dhis2_timeshift_move_future_to_buffer_core();
END;
$$;

	------------------------ Move data back from buffer year to current peroid ---------------------------------------------------------------
	---- Move all buffer  data to the current period
	-- to be used by corn each peroid 
	Drop function if EXISTS dhis2_timeshift_buffer_to_current (period_type TEXT);
	CREATE FUNCTION dhis2_timeshift_buffer_to_current (period_type TEXT)
	RETURNS boolean LANGUAGE plpgsql
	AS
	$$

	DECLARE

	BEGIN
		WITH buffer_year_peroid
		AS (
			SELECT left(cast(periodid AS TEXT), - 2)::BIGINT AS old_peroid
				,periodid
				,periodtypeid
				,startdate
				,enddate
				,date_part('year', startdate) AS buffer_year
			FROM period
			WHERE date_part('year', startdate) = (
					SELECT date_part('year', min(pp.startdate))
					FROM period pp
					)
			)
			,feature_year_peroid
		AS (
			SELECT periodid::BIGINT AS pp
				,periodtypeid
				,startdate
				,enddate
			FROM period
			WHERE date_part('year', startdate) = date_part('year', now())
			)
			,pre_update
		AS (
			SELECT old_peroid
				,bf_year.periodid AS new_peroid
				,f_year.startdate AS f_startdate
				,f_year.enddate AS f_enddate
				,bf_year.periodtypeid
				,pp AS feature_period
				,bf_year.startdate AS bf_startdate
				,bf_year.enddate AS bf_enddate
			FROM buffer_year_peroid bf_year
			JOIN feature_year_peroid f_year ON f_year.pp = bf_year.old_peroid
			)
			,dv2
		AS (
			SELECT dataelementid
				,sourceid
				,categoryoptioncomboid
				,attributeoptioncomboid
				,value
				,dv.periodid
			FROM datavalue dv
			INNER JOIN pre_update ON dv.periodid = pre_update.new_peroid
			)
		--select * from pre_update
		UPDATE datavalue dv
		SET periodid = pre_update.feature_period
		FROM pre_update
		INNER JOIN dv2 ON dv2.periodid = pre_update.new_peroid
		LEFT JOIN periodtype pt ON pre_update.periodtypeid = pt.periodtypeid
		WHERE dv.periodid = pre_update.new_peroid
			AND pre_update.f_startdate::DATE <= now()::DATE
			AND dv2.dataelementid = dv.dataelementid
			AND dv2.sourceid = dv.sourceid
			AND dv2.categoryoptioncomboid = dv.categoryoptioncomboid
			AND dv2.attributeoptioncomboid = dv.attributeoptioncomboid
			AND dv2.value = dv.value
			AND pt.name = period_type;

		RETURN TRUE;
	END $$;
