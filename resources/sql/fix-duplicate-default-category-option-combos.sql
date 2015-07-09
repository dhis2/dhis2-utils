
-- Delete and update data values for which two attribute option combos are duplicates

-- Delete null data values

delete from datavalue where value is null and comment is null;

-- Set lastupdated to far in the past where not set

update datavalue set lastupdated = '1900-01-01' where lastupdated is null;

-- Delete the oldest duplicate data value based on attribute option combo

delete from datavalue dv1
where dv1.attributeoptioncomboid in (16,498)
and exists (
  select * from datavalue dv2
  where dv1.dataelementid = dv2.dataelementid
  and dv1.periodid = dv2.periodid
  and dv1.sourceid = dv2.sourceid
  and dv1.categoryoptioncomboid = dv2.categoryoptioncomboid
  and dv1.attributeoptioncomboid != dv2.attributeoptioncomboid
  and dv2.attributeoptioncomboid in (16,498)
  and dv2.lastupdated >= dv1.lastupdated
);

-- Delete the oldest duplicate data value based on category option combo

delete from datavalue dv1
where dv1.categoryoptioncomboid in (16,498)
and exists (
  select * from datavalue dv2
  where dv1.dataelementid = dv2.dataelementid
  and dv1.periodid = dv2.periodid
  and dv1.sourceid = dv2.sourceid
  and dv1.categoryoptioncomboid != dv2.categoryoptioncomboid
  and dv1.attributeoptioncomboid = dv2.attributeoptioncomboid
  and dv2.categoryoptioncomboid in (16,498)
  and dv2.lastupdated >= dv1.lastupdated
);

-- Delete duplicate data value audit based on attribute option combo

delete from datavalueaudit dv1
where dv1.attributeoptioncomboid in (16,498)
and exists (
  select * from datavalueaudit dv2
  where dv1.dataelementid = dv2.dataelementid
  and dv1.periodid = dv2.periodid
  and dv1.organisationunitid = dv2.organisationunitid
  and dv1.categoryoptioncomboid = dv2.categoryoptioncomboid
  and dv1.attributeoptioncomboid != dv2.attributeoptioncomboid
  and dv2.attributeoptioncomboid in (16,498)
);

-- Delete duplicate data value audit based on category option combo

delete from datavalueaudit dv1
where dv1.categoryoptioncomboid in (16,498)
and exists (
  select * from datavalueaudit dv2
  where dv1.dataelementid = dv2.dataelementid
  and dv1.periodid = dv2.periodid
  and dv1.organisationunitid = dv2.organisationunitid
  and dv1.categoryoptioncomboid != dv2.categoryoptioncomboid
  and dv1.attributeoptioncomboid = dv2.attributeoptioncomboid
  and dv2.categoryoptioncomboid in (16,498)
);

-- Delete the oldest duplicate complete data set registrations

delete from completedatasetregistration cr1
where cr1.attributeoptioncomboid in (16,498)
and exists (
  select * from completedatasetregistration cr2
  where cr1.datasetid=cr2.datasetid
  and cr1.periodid=cr2.periodid
  and cr1.sourceid=cr2.sourceid
  and cr1.attributeoptioncomboid != cr2.attributeoptioncomboid
  and cr1.attributeoptioncomboid in (16,498)
  and cr1.date >= cr2.date
);

-- Delete min max data element duplicates based on category option combo

delete from minmaxdataelement md1
where md1.categoryoptioncomboid in (16,498)
and exists (
  select * from minmaxdataelement md2
  where md1.dataelementid = md2.dataelementid
  and md1.sourceid = md2.sourceid
  and md1.categoryoptioncomboid != md2.categoryoptioncomboid
  and md2.categoryoptioncomboid in (16,498)
);

-- Moved data values from one attribute option combo to the other

update datavalue set attributeoptioncomboid = 16 where attributeoptioncomboid = 498;
update datavalueaudit set attributeoptioncomboid = 16 where attributeoptioncomboid = 498;

-- Moved data values from one category option combo to the other

update datavalue set categoryoptioncomboid = 16 where categoryoptioncomboid = 498;
update datavalueaudit set categoryoptioncomboid = 16 where categoryoptioncomboid = 498;
update completedatasetregistration set attributeoptioncomboid = 16 where attributeoptioncomboid = 498;
update minmaxdataelement set categoryoptioncomboid = 16 where categoryoptioncomboid = 498;

-- Delete old category option combo and link table rows

delete from categorycombos_optioncombos where categoryoptioncomboid=498;
delete from categoryoptioncombos_categoryoptions where categoryoptioncomboid=498;
delete from categoryoptioncombo where categoryoptioncomboid=498;

-- List custom data entry forms which must be updated

select ds.name, df.name from dataentryform df
inner join dataset ds on ds.dataentryform=df.dataentryformid
where df.htmlcode ~ 'WeuRNmvZSXe';

-- Remember to update category option combos from data admin > maintenance
