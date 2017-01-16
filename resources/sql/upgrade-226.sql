
-- 2.26 upgrade script

-- Set data value 'created' and 'lastupdated' columns to now if null and set to not null

update datavalue set created = now()::timestamp where created is null;
alter table datavalue alter column created set not null;

update datavalue set lastupdated = now()::timestamp where lastupdated is null;
alter table datavalue alter column lastupdated set not null;

-- Upgrade coordinate tracked entity data values to use brackets

update trackedentitydatavalue
set value = '[' || value || ']'
where dataelementid in (
  select dataelementid from dataelement
  where valuetype='COORDINATE')
and value is not null
and value ~ ','
and value not like '\[%\]';

-- Upgrade coordinate tracked entity attribute values to use brackets

update trackedentityattributevalue
set value = '[' || value || ']'
where trackedentityattributeid in (
  select trackedentityattributeid from trackedentityattribute
  where valuetype='COORDINATE')
and value is not null
and value ~ ','
and value not like '\[%\]';

-- Upgrade authority for messaging module

insert into userroleauthorities 
select userroleid, 'M_dhis-web-messaging' FROM userroleauthorities WHERE authority = 'M_dhis-web-dashboard-integration';
