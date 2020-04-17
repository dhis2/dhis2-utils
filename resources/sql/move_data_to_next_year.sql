
-- SQL script for moving data from one year to the next. 
-- Useful for updating demo databases with sample data.

-- (Write) Move startdate and enddate in period to next year
-- Change the year to reflect the current time. Periods are
-- moved one year at the time to avoid unique constraint violations.

update period set 
startdate = (startdate + interval '1 year')::date,
enddate = (enddate + interval '1 year')::date
where date_part('year', startdate)::int = 2019;

update period set 
startdate = (startdate + interval '1 year')::date,
enddate = (enddate + interval '1 year')::date
where date_part('year', startdate)::int = 2018;

update period set -- Handle financial year data
startdate = (startdate + interval '1 year')::date,
enddate = (enddate + interval '1 year')::date
where date_part('year', startdate)::int = 2017;

-- (Write) Move programstageinstance

update programstageinstance set 
duedate = (duedate + interval '1 year'),
executiondate = (executiondate + interval '1 year'),
completeddate = (completeddate + interval '1 year');

-- (Write) Move programinstance to next year

update programinstance set
incidentdate = (incidentdate + interval '1 year'),
enrollmentdate = (enrollmentdate + interval '1 year'),
enddate = (enddate + interval '1 year');

-- (Write) Move interpretations created / lastupdated to next year

update interpretation set created = (created + interval '1 year');
update interpretation set lastupdated = created;

-- (Write) Move favorite start/end dates to next year

update mapview set startdate = (startdate + interval '1 year') where startdate is not null;
update mapview set enddate = (enddate + interval '1 year') where enddate is not null;

update eventreport set startdate = (startdate + interval '1 year') where startdate is not null;
update eventreport set enddate = (enddate + interval '1 year') where enddate is not null;

update eventchart set startdate = (startdate + interval '1 year') where startdate is not null;
update eventchart set enddate = (enddate + interval '1 year') where enddate is not null;

-- (Write) Move date event values to next year

update trackedentitydatavalue set value = to_char((value::date + interval '1 year'), 'YYYY-MM-dd') 
where dataelementid in (
  select dataelementid from dataelement where valuetype in ('DATE','DATETIME') and domaintype = 'TRACKER'
);

-- Vacuum to remove dead tuples

vacuum period;
vacuum programstageinstance;
vacuum programinstance;
vacuum interpretation;
vacuum mapview;
vacuum eventreport;
vacuum eventchart;
vacuum trackedentitydatavalue;

