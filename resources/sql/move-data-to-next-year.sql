
-- SQL script for moving data from one year to the next. Useful for 
-- updating demo databases with sample data.

-- (Write) Move startdate and enddate in period to next year

update period set 
startdate = (startdate + interval '1 year')::date,
enddate = (enddate + interval '1 year')::date;

-- (Write) Move programstageinstance and programinstance to next year

update programstageinstance set 
duedate = (duedate + interval '1 year'),
executiondate = (executiondate + interval '1 year'),
completeddate = (completeddate + interval '1 year'),
created = (created + interval '1 year'),
lastupdated = (lastupdated + interval '1 year');

update programinstance set
incidentdate = (incidentdate + interval '1 year'),
enrollmentdate = (enrollmentdate + interval '1 year'),
enddate = (enddate + interval '1 year'),
created = (created + interval '1 year'),
lastupdated = (lastupdated + interval '1 year');

-- (Write) Move interpretations created / lastupdated to next year

update interpretation set created = (created + interval '1 year');
update interpretation set lastupdated=created;
