
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
