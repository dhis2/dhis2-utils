
-- Set org unit of program instance to org unit of tracked entity instance

update programinstance pi
set organisationunitid = (
  select organisationunitid from trackedentityinstance tei
  where pi.trackedentityinstanceid = tei.trackedentityinstanceid)
where pi.organisationunitid is null;

-- Upgrade program data entry form foreign keys

alter table programstage drop constraint fk_programstage_dataentryform;
alter table programstage add constraint fk_programstage_dataentryform foreign key (dataentryform) references dataentryform (dataentryformid) match SIMPLE on update no action on delete no action;

alter table trackedentityform drop constraint fk_trackedentityform_dataentryformid;
alter table trackedentityform add constraint fk_trackedentityform_dataentryformid foreign key (dataentryform) references dataentryform (dataentryformid) match SIMPLE on update no action on delete no action;
