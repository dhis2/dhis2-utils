
-- Move population data from last year to this year

-- If specific data level is required update the _orgunitstructure resource table

-- Replace first periodid with current year, replace second periodid with last year, replace dataset.name with population dataset name, replace data level as required

delete from datavalue where periodid=234430 and dataelementid in (
  select dataelementid from datasetmembers
  join dataset using(datasetid)
  where dataset.name='Population estimates' )
and sourceid in (
  select os.organisationunitid from organisationunit ou
  join _orgunitstructure os using(organisationunitid)
  where os.level = 4);

insert into datavalue(dataelementid,periodid,sourceid,categoryoptioncomboid,value,storedby,lastupdated,comment,followup)
select dataelementid,234430 as periodid,sourceid,categoryoptioncomboid,ceil(cast(value as double precision)*1.029) as value,storedby,lastupdated,null,false
from datavalue
where periodid=112482 and dataelementid in (
  select dataelementid from datasetmembers
  join dataset using(datasetid)
  where dataset.name='Population estimates' )
and sourceid in (
  select os.organisationunitid from organisationunit ou
  join _orgunitstructure os using(organisationunitid)
  where os.level = 4);

