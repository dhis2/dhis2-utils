
-- 2.26 upgrade script

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
