
-- Delete and update data values for which two attribute option combos are duplicates

-- Delete null data values

delete from datavalue where value is null;

-- Set lastupdated to far in the past where not set

update datavalue set lastupdated = '1900-01-01' where lastupdated is null;

-- Delete the oldest duplicate based on attribute option combo

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

-- Delete the oldest duplicate based on category option combo

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

-- Moved data values from one attribute option combo to the other

update datavalue set attributeoptioncomboid = 16 where attributeoptioncomboid = 498;

-- Moved data values from one category option combo to the other

update datavalue set categoryoptioncomboid = 16 where categoryoptioncomboid = 498;
