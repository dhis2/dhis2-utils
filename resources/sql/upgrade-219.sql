
-- Set org unit of program instance to org unit of tracked entity instance

alter table programinstance add column organisationunitid integer;

update programinstance pi
set organisationunitid = (
  select organisationunitid from trackedentityinstance tei
  where pi.trackedentityinstanceid = tei.trackedentityinstanceid)
where pi.organisationunitid is null;
