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

-- Delete events and releted entities

delete from trackedentitydatavalueaudit tdva
where tdva.programstageinstanceid in (
  select psi.programstageinstanceid
  from programstageinstance psi
  where psi.executiondate 
  or psi.executiondate > '2100-01-01');
 
delete from programmessage pm
where pm.programstageinstanceid in (
  select psi.programstageinstanceid
  from programstageinstance psi
  where psi.executiondate < '1960-01-01'
  or psi.executiondate > '2100-01-01'); 

delete from programstageinstance psi
where psi.executiondate < '1960-01-01'
or psi.executiondate > '2100-01-01';
