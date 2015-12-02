
-- Delete lowest numeric duplicate data value (replace UIDs)

delete from datavalue dv1
using organisationunit ou1, dataelement de1
where dv1.sourceid = ou1.organisationunitid
and dv1.dataelementid = de1.dataelementid
and ou1.uid in ('F9q9oERB2jd','DGjspVpNRWY')
and de1.valuetype in ('NUMBER','UNIT_INTERVAL','PERCENTAGE','INTEGER',
'INTEGER_POSITIVE','INTEGER_NEGATIVE','INTEGER_ZERO_OR_POSITIVE')
and exists (
  select * from datavalue dv2
  inner join organisationunit ou2 on dv2.sourceid = ou2.organisationunitid
  where dv1.dataelementid = dv2.dataelementid
  and dv1.periodid = dv2.periodid
  and dv1.sourceid != dv2.sourceid
  and ou2.uid in ('F9q9oERB2jd','DGjspVpNRWY')
  and dv1.categoryoptioncomboid = dv2.categoryoptioncomboid
  and dv1.attributeoptioncomboid = dv2.attributeoptioncomboid
  and dv2.value is not null
  and dv2.value > dv1.value);

-- Delete oldest textual duplicate data value (replace UIDs)

delete from datavalue dv1
using organisationunit ou1, dataelement de1
where dv1.sourceid = ou1.organisationunitid
and dv1.dataelementid = de1.dataelementid
and ou1.uid in ('F9q9oERB2jd','DGjspVpNRWY')
and de1.valuetype in ('TEXT','LONG_TEXT','LETTER','PHONE_NUMBER','EMAIL','BOOLEAN',
'TRUE_ONLY','DATE','DATETIME','TRACKER_ASSOCIATE','USERNAME','FILE_RESOURCE','COORDINATE')
and exists (
  select * from datavalue dv2
  inner join organisationunit ou2 on dv2.sourceid = ou2.organisationunitid
  where dv1.dataelementid = dv2.dataelementid
  and dv1.periodid = dv2.periodid
  and dv1.sourceid != dv2.sourceid
  and ou2.uid in ('F9q9oERB2jd','DGjspVpNRWY')
  and dv1.categoryoptioncomboid = dv2.categoryoptioncomboid
  and dv1.attributeoptioncomboid = dv2.attributeoptioncomboid
  and dv2.value is not null
  and dv2.lastupdated >= dv1.lastupdated);

-- Delete data value audit (replace UID for org unit to remove)

delete from datavalueaudit dv1
using organisationunit ou1
where dv1.organisationunitid = ou1.organisationunitid
and ou1.uid = 'DGjspVpNRWY';

-- Delete the oldest complete data set registration (replace UIDs)

delete from completedatasetregistration cr1
using organisationunit ou1
where cr1.sourceid = ou1.organisationunitid
and ou1.uid in ('F9q9oERB2jd','DGjspVpNRWY')
and exists (
  select * from completedatasetregistration cr2
  inner join organisationunit ou2 on cr2.sourceid = ou2.organisationunitid
  where cr1.datasetid = cr2.datasetid
  and cr1.periodid = cr2.periodid
  and cr1.sourceid != cr2.sourceid
  and ou2.uid in ('F9q9oERB2jd','DGjspVpNRWY')
  and cr1.attributeoptioncomboid = cr2.attributeoptioncomboid
  and cr2.date >= cr1.date
);

-- Delete data approval records for org unit to remove

delete from dataapproval where organisationunitid = (
  select organisationunitid from organisationunit where uid = 'DGjspVpNRWY');

-- Move data values from org unit to remove to org unit to keep

update datavalue set sourceid = (
  select organisationunitid from organisationunit where uid = 'F9q9oERB2jd')
where sourceid = (
  select organisationunitid from organisationunit where uid = 'DGjspVpNRWY');

-- Move complete data set registrations from org unit to remove to org unit to keep

update completedatasetregistration set sourceid = (
  select organisationunitid from organisationunit where uid = 'F9q9oERB2jd')
where sourceid = (
  select organisationunitid from organisationunit where uid = 'DGjspVpNRWY');

-- Now delete org unit to remove through API to clear up meta-data foreign constraints
