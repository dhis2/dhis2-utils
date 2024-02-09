--
-- Script for deleting data values and events out of reasonable range
--

-- Delete data values, complete registrations and data approvals

delete from dataapproval da
where da.periodid in (
  select p.periodid
  from period p
  where p.enddate < '1960-01-01'
  or p.startdate > '2100-01-01');

delete from completedatasetregistration dr
where dr.periodid in (
  select p.periodid
  from period p
  where p.enddate < '1960-01-01'
  or p.startdate > '2100-01-01');

delete from datavalue dv
where dv.periodid in (
  select p.periodid
  from period p
  where p.enddate < '1960-01-01'
  or p.startdate > '2100-01-01');

-- Delete periods

delete from period p
where p.enddate < '1960-01-01'
or p.startdate > '2100-01-01';

-- Delete events and related entities

create or replace view events_out_of_range as
select psi.programstageinstanceid
from programstageinstance psi
where psi.executiondate < '1960-01-01'
or psi.executiondate > '2100-01-01'
or (psi.status = 'SCHEDULE' and (psi.duedate < '1960-01-01' or psi.duedate > '2100-01-01'));

delete from trackedentitydatavalueaudit tdva
where tdva.programstageinstanceid in (
  select programstageinstanceid from events_out_of_range);
 
delete from programmessage pm
where pm.programstageinstanceid in (
  select programstageinstanceid from events_out_of_range);

delete from programstageinstance psi
where psi.programstageinstanceid in (
  select programstageinstanceid from events_out_of_range);

drop view if exists events_out_of_range;
