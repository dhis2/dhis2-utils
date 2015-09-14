
-- Get periods with equal period type and start date (not valid)

select p1.periodtypeid, p1.startdate, p1.enddate 
from period p1
inner join period p2
on p1.periodtypeid = p2.periodtypeid
and p1.startdate = p2.startdate
where p1.periodid != p2.periodid
order by p1.periodtypeid, p1.startdate, p1.enddate;

-- Get name of datasets for a dataelement

select ds.name from dataset ds
join datasetmembers dm on (ds.datasetid=dm.datasetid) 
join dataelement de on (dm.dataelementid=de.dataelementid)
where de.name = 'Adverse Events Following Immunization';

-- Get dataelements not part of any dataset

select dataelementid, name from dataelement where dataelementid not in (
select dataelementid from datasetmembers)
and domaintype='aggregate'
order by name;

-- Get category combo with no data elements

select cc.categorycomboid, cc.name from categorycombo cc where cc.categorycomboid not in (
select distinct categorycomboid from dataelement);

-- Get dataelement name and category combo for a section

select de.name as dataelementname, cc.name as categorycomboname from dataelement de
join categorycombo cc on(de.categorycomboid=cc.categorycomboid)
join sectiondataelements sd on(de.dataelementid=sd.dataelementid)
join section sc on(sd.sectionid=sc.sectionid)
where sc.name = 'OPD Diagnoses';

-- Get data elements and number of data values sorted ascending

select distinct d.dataelementid, d.name, count(v.*) as cnt from datavalue v 
join dataelement d on(v.dataelementid=d.dataelementid) 
group by d.dataelementid, d.name 
order by cnt asc;

-- Get dataset memberships for data elements with more than one membership

select de.name, ds.name from dataelement de
join datasetmembers dm on(de.dataelementid=dm.dataelementid)
join dataset ds on(dm.datasetid=ds.datasetid)
where de.dataelementid in (
  select de.dataelementid from dataelement de
  join datasetmembers ds on (de.dataelementid=ds.dataelementid)
  group by de.dataelementid
  having(count(de.dataelementid) > 1) )
order by de.name;

-- Get dataelements which are members of a section but not the section's dataset

select de.name as dataelementname, sc.name as sectionname, ds.name as datasetname from sectiondataelements sd
join dataelement de on(sd.dataelementid=de.dataelementid)
join section sc on (sd.sectionid=sc.sectionid)
join dataset ds on (sc.datasetid=ds.datasetid)
where sd.dataelementid not in (
  select dm.dataelementid from datasetmembers dm
  join dataset ds on(dm.datasetid=ds.datasetid)
  where sc.datasetid=ds.datasetid)
order by ds.name, de.name;

-- Get categories with category memberships

select co.name, c.name from dataelementcategory c 
join categories_categoryoptions using(categoryid) 
join dataelementcategoryoption co using(categoryoptionid) order by co.name, c.name;

-- Get orgunit groups which an orgunit is member of

select * from orgunitgroup g
join orgunitgroupmembers m using(orgunitgroupid)
join organisationunit o using (organisationunitid)
where o.name = 'Mandera District Hospital';

-- Get reports which uses report table

select * from report r
join reportreporttables rr using(reportid)
join reporttable t using(reporttableid)
where t.name='Indicators';

-- Show collection frequency of data elements with average aggregation operator

select distinct de.name, periodtype.name 
from dataelement de 
join datasetmembers using (dataelementid) 
join dataset using (datasetid) 
join periodtype using(periodtypeid) 
where de.aggregationtype = 'average';

-- Get category option groups which are members of more than one group set

select categoryoptiongroupid, count(categoryoptiongroupid) as count
from categoryoptiongroupsetmembers
group by categoryoptiongroupid
having count(categoryoptiongroupid) > 1;

-- Get missing items in a list / missing options in a category by looking at the sort_order and the max sort_order value

select * from (
select generate_series
from generate_series(1,1634)
) s
left join categories_categoryoptions cco on (
  s.generate_series=cco.sort_order
  and cco.categoryid=492298)
where cco.sort_order is null;

-- Identify sections where sort_order is wrong

select ds.name as dataset, s.name as section, sd.sectionid, 
max(sd.sort_order) as max_sort_order, count(distinct dataelementid) as dataelement_count
from sectiondataelements sd
inner join section s on sd.sectionid=s.sectionid
inner join dataset ds on s.datasetid=ds.datasetid
group by ds.name, s.name, sd.sectionid
order by max(sd.sort_order) desc;

-- Get program indicators where expression contains 

select pi.uid as indicatoruid, pi.name as indicator, de.uid as dataelementuid, de.name as dataelement
from programindicator pi, dataelement de
where de.valuetype != 'int'
and pi.expression like ( '%'||de.uid||'%')
order by pi.name, de.name;

-- Category combo and option combo overview

select c.name as categorycombo, n.categoryoptioncomboname, n.categoryoptioncomboid  from _categoryoptioncomboname n 
join categorycombos_optioncombos co on (n.categoryoptioncomboid=co.categoryoptioncomboid)
join categorycombo c on (co.categorycomboid=c.categorycomboid)
order by c.name, n.categoryoptioncomboname;
