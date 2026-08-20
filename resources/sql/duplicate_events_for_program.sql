
-- Duplicate all events for a program

-- Supports DHIS2 version 2.42

-- Update program UID to match environment

insert into event(
   eventid,
   enrollmentid,
   programstageid,
   scheduleddate,
   occurreddate,
   organisationunitid,
   status,
   completeddate,
   uid,
   created,
   lastupdated,
   attributeoptioncomboid,
   storedby,
   completedby,
   deleted,
   code,
   createdatclient,
   lastupdatedatclient,
   geometry,
   lastsynchronized,
   eventdatavalues,
   assigneduserid,
   createdbyuserinfo,
   lastupdatedbyuserinfo)
select
   nextval('programstageinstance_sequence'),
   ev.enrollmentid,
   ev.programstageid,
   ev.scheduleddate + interval '1 day' as scheduleddate,
   ev.occurreddate + interval '1 day' as occurreddate,
   ev.organisationunitid,
   ev.status,
   ev.completeddate + interval '1 day' as completeddate,
   uid() as uid,
   ev.created + interval '1 day' as created,
   ev.lastupdated + interval '1 day' as lastupdated,
   ev.attributeoptioncomboid,
   'script-run-01' as storedby,
   ev.completedby,
   ev.deleted,
   ev.code,
   ev.createdatclient + interval '1 day' as createdatclient,
   ev.lastupdatedatclient + interval '1 day' as lastupdatedatclient,
   ev.geometry,
   ev.lastsynchronized,
   ev.eventdatavalues,
   ev.assigneduserid,
   ev.createdbyuserinfo,
   ev.lastupdatedbyuserinfo
from
   event ev
   inner join enrollment er on ev.enrollmentid = er.enrollmentid 
   inner join program pr on er.programid = pr.programid 
   where pr.uid = 'eBAyeGv0exc';
