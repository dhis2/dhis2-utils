
-- DATA ELEMENTS

-- Data elements and frequency with average agg operator (higher than yearly negative for data mart performance)

select d.dataelementid, d.name as dataelement, pt.name as periodtype from dataelement d 
join datasetmembers dsm on d.dataelementid=dsm.dataelementid 
join dataset ds on dsm.datasetid=ds.datasetid 
join periodtype pt on ds.periodtypeid = pt.periodtypeid 
where d.aggregationtype = 'average'
order by pt.name;

-- Data elements with aggregation levels

select d.dataelementid, d.name, dal.aggregationlevel from dataelementaggregationlevels dal 
join dataelement d on dal.dataelementid=d.dataelementid 
order by name, aggregationlevel;

-- Data elements with less than 100 data values

select de.dataelementid, de.name, (select count(*) from datavalue dv where de.dataelementid=dv.dataelementid) as count 
from dataelement de
where (select count(*) from datavalue dv where de.dataelementid=dv.dataelementid) < 100
order by count;

-- Number of data elements with less than 100 data values

select count(*) from dataelement de
where (select count(*) from datavalue dv where de.dataelementid=dv.dataelementid) < 100;

-- Duplicate data element codes

select code, count(code) as count
from dataelement
group by code
order by count desc;

-- Display overview of data elements and related category option combos

select de.uid as dataelement_uid, de.name as dataelement_name, de.code as dataelement_code, coc.uid as optioncombo_uid, cocn.categoryoptioncomboname as optioncombo_name 
from _dataelementcategoryoptioncombo dcoc 
inner join dataelement de on dcoc.dataelementuid=de.uid 
inner join categoryoptioncombo coc on dcoc.categoryoptioncombouid=coc.uid 
inner join _categoryoptioncomboname cocn on coc.categoryoptioncomboid=cocn.categoryoptioncomboid 
order by de.name;

-- (Write) Remove data elements from data sets which are not part of sections

delete from datasetmembers dsm
where dataelementid not in (
  select dataelementid from sectiondataelements ds
  inner join section s on (ds.sectionid=s.sectionid)
  where s.datasetid=dsm.datasetid)
and dsm.datasetid=1979200;


-- CATEGORIES

-- Exploded category option combo view

select cc.categorycomboid, cc.name as categorycomboname, cn.* from _categoryoptioncomboname cn
join categorycombos_optioncombos co using(categoryoptioncomboid)
join categorycombo cc using(categorycomboid)
order by categorycomboname, categoryoptioncomboname;

-- Display category option combo identifier and name

select cc.categoryoptioncomboid as id, uid, categoryoptioncomboname as name, code
from categoryoptioncombo cc
join _categoryoptioncomboname cn
on (cc.categoryoptioncomboid=cn.categoryoptioncomboid);

-- Display overview of category option combo

select coc.categoryoptioncomboid as coc_id, coc.uid as coc_uid, co.categoryoptionid as co_id, co.name as co_name, ca.categoryid as ca_id, ca.name as ca_name, cc.categorycomboid as cc_id, cc.name as cc_name
from categoryoptioncombo coc 
inner join categoryoptioncombos_categoryoptions coo on coc.categoryoptioncomboid=coo.categoryoptioncomboid
inner join dataelementcategoryoption co on coo.categoryoptionid=co.categoryoptionid
inner join categories_categoryoptions cco on co.categoryoptionid=cco.categoryoptionid
inner join dataelementcategory ca on cco.categoryid=ca.categoryid
inner join categorycombos_optioncombos ccoc on coc.categoryoptioncomboid=ccoc.categoryoptioncomboid
inner join categorycombo cc on ccoc.categorycomboid=cc.categorycomboid
where coc.categoryoptioncomboid=2118430;

-- Display overview of category option combos

select coc.uid as optioncombo_uid, cocn.categoryoptioncomboname as optioncombo_nafme, cc.uid as categorycombo_uid, cc.name as categorycombo_name 
from categoryoptioncombo coc 
inner join _categoryoptioncomboname cocn on coc.categoryoptioncomboid=cocn.categoryoptioncomboid 
inner join categorycombos_optioncombos ccoc on coc.categoryoptioncomboid=ccoc.categoryoptioncomboid 
inner join categorycombo cc on ccoc.categorycomboid=cc.categorycomboid;

-- Get category option combos linked to category option

select coc.categoryoptioncomboid as coc_id, coc.uid as coc_uid, co.categoryoptionid as co_id, co.name as co_name
from categoryoptioncombo coc 
inner join categoryoptioncombos_categoryoptions coo on coc.categoryoptioncomboid=coo.categoryoptioncomboid
inner join dataelementcategoryoption co on coo.categoryoptionid=co.categoryoptionid
where co.uid='LPeJEUjotaB';

-- Category option combo count per category option

select count(cocco.categoryoptioncomboid) as cat_option_combo_count, cocco.categoryoptionid as cat_option_id, co.name as cat_option_name
from categoryoptioncombos_categoryoptions cocco 
inner join dataelementcategoryoption co on cocco.categoryoptionid=co.categoryoptionid 
group by cocco.categoryoptionid, co.name 
order by count(categoryoptioncomboid) desc 
limit 100;

-- Category option combo count per category combo

select cc.name as cat_combo_name, count(ccoc.categoryoptioncomboid) as cat_option_combo_count
from categorycombo cc
inner join categorycombos_optioncombos ccoc on cc.categorycomboid = ccoc.categorycomboid
group by cc.name
order by cat_option_combo_count desc;

-- Exploded _datasetorganisationunitcategory view

select ds.uid as ds_uid, ds.name as ds_name, ou.uid as ou_uid, ou.name as ou_name, oulev2.name as oulev2_name, oulev3.name as oulev3_name, 
coc.uid as aoc_uid, coc.name as aoc_name, dsc.costartdate, dsc.coenddate
from _datasetorganisationunitcategory dsc
inner join dataset ds on dsc.datasetid=ds.datasetid
inner join _orgunitstructure ous on dsc.organisationunitid=ous.organisationunitid
inner join organisationunit ou on ous.organisationunitid=ou.organisationunitid
inner join organisationunit oulev2 on ous.idlevel2=oulev2.organisationunitid
inner join organisationunit oulev3 on ous.idlevel3=oulev3.organisationunitid
inner join categoryoptioncombo coc on dsc.attributeoptioncomboid=coc.categoryoptioncomboid;

-- Exploded analytics_completenesstarget view

select ct.*, ds.name as ds_name, oulev2.name as oulev2_name, oulev3.name as oulev3_name, coc.name as aoc_name
from analytics_completenesstarget ct
inner join dataset ds on ct.dx=ds.uid
inner join organisationunit oulev2 on ct.uidlevel2=oulev2.uid
inner join organisationunit oulev3 on ct.uidlevel3=oulev3.uid
inner join categoryoptioncombo coc on ct.ao=coc.uid

-- Duplicate category names

select c.name, count(c.uid) as row_count, array_agg(c.uid) as uids
from dataelementcategory c
group by c.name
having count(c.uid) > 1
order by row_count desc;


-- DATA SETS

select ds.uid as ds_uid, ds.name as ds_name, (
  select count(*)
  from datasetelement dse
  where ds.datasetid = dse.datasetid) as de_count
from dataset ds
order by de_count desc;


-- ORGANISATION UNITS

-- Facility overview

select distinct ous.idlevel5 as internalid, ou.uid, ou.code, ou.name, ougs.type, ougs.ownership,
ou2.name as province, ou3.name as county, ou4.name as district, ou.coordinates as longitide_latitude
from _orgunitstructure ous
left join organisationunit ou on ous.organisationunitid=ou.organisationunitid
left join organisationunit ou2 on ous.idlevel2=ou2.organisationunitid
left join organisationunit ou3 on ous.idlevel3=ou3.organisationunitid
left join organisationunit ou4 on ous.idlevel4=ou4.organisationunitid
left join _organisationunitgroupsetstructure ougs on ous.organisationunitid=ougs.organisationunitid
where ous.level=5
order by province, county, district, ou.name;

-- Turn longitude/latitude around for organisationunit coordinates (adjust the like clause)

update organisationunit set coordinates=regexp_replace(coordinates,'\[(.+?\..+?),(.+?\..+?)\]','[\2,\1]')
where coordinates like '[0%'
and featuretype='Point';

-- Fetch longitude/latitude from organisationunit

select name, coordinates, 
cast( regexp_replace( coordinates, '\[(-?\d+\.?\d*)[,](-?\d+\.?\d*)\]', '\1' ) as double precision ) as longitude,
cast( regexp_replace( coordinates, '\[(-?\d+\.?\d*)[,](-?\d+\.?\d*)\]', '\2' ) as double precision ) as latitude 
from organisationunit
where featuretype='Point';

-- Identify empty groups

select 'Data element group' as type, o.name as name
from dataelementgroup o
where not exists (
  select * from dataelementgroupmembers
  where dataelementgroupid=o.dataelementgroupid)
union all
select 'Indicator group' as type, o.name as name
from indicatorgroup o
where not exists (
  select * from indicatorgroupmembers
  where indicatorgroupid=o.indicatorgroupid)
union all
select 'Organisation unit group' as type, o.name as name
from orgunitgroup o
where not exists (
  select * from orgunitgroupmembers
  where orgunitgroupid=o.orgunitgroupid)
order by type,name;

-- Nullify coordinates with longitude outside range (adjust where clause values)

update organisationunit set coordinates=null
where featuretype='Point'
and (
  cast(substring(coordinates from '\[(.+?\..+?),.+?\..+?\]') as double precision) < 32
  or cast(substring(coordinates from '\[(.+?\..+?),.+?\..+?\]') as double precision) > 43
);


-- USERS

-- Compare user roles (lists what is in the first role but not in the second)

select authority from userroleauthorities where userroleid=33706 and authority not in (select authority from userroleauthorities where userroleid=21504);

-- User overview (Postgres only)

select u.username, u.lastlogin, u.selfregistered, ui.surname, ui.firstname, ui.email, ui.phonenumber, ui.jobtitle, (
  select array_to_string( array(
    select name from userrole ur
    join userrolemembers urm using(userroleid)
    where urm.userid=u.userid), ', ' )
  )  as userroles, (
  select array_to_string( array(
    select name from organisationunit ou
    join usermembership um using(ofrganisationunitid)
    where um.userinfoid=ui.userinfoid), ', ' )
  ) as orgunits
from users u 
join userinfo ui on u.userid=ui.userinfoid
order by u.username;

-- Users in user role

select u.userid, u.username, ui.firstname, ui.surname from users u 
inner join userinfo ui on u.userid=ui.userinfoid 
inner join userrolemembers urm on u.userid=urm.userid 
inner join userrole ur on urm.userroleid=ur.userroleid 
where ur.name='UserRoleName';

-- Users with ALL authority

select u.userid, u.username, ui.firstname, ui.surname from users u 
inner join userinfo ui on u.userid=ui.userinfoid
where u.userid in (
  select urm.userid from userrolemembers urm 
  inner join userrole ur on urm.userroleid=ur.userroleid
  inner join userroleauthorities ura on ur.userroleid=ura.userroleid 
  where ura.authority = 'ALL'
);

-- User roles with authority

select ur.userroleid, ur.name
from userrole ur
inner join userroleauthorities ura on ur.userroleid=ura.userroleid 
where ura.authority = 'ALL';

-- (Write) Bcrypt set password to "district" for admin user up to 2.37

update users set password='$2a$10$wjLPViry3bkYEcjwGRqnYO1bT2Kl.ZY0kO.fwFDfMX53hitfx5.3C', disabled = false where username='admin';

-- (Write) Bcrypt set password to "district" for admin user after 2.37

update userinfo set password='$2a$10$wjLPViry3bkYEcjwGRqnYO1bT2Kl.ZY0kO.fwFDfMX53hitfx5.3C', disabled = false where username='admin';

-- (Write) Add user to first user role with ALl authority 

insert into userrolemembers (userid, userroleid)
select userid, userroleid 
from (
  select u.userid 
  from users u 
  where u.username = 'admin'
  limit 1) as userid, (

  select ur.userroleid
  from userrole ur 
  inner join userroleauthorities ura on ur.userroleid=ura.userroleid 
  where ura.authority = 'ALL'
  limit 1) as userroleid;


-- VALIDATION RULES

-- Display validation rules which includes the given data element uid

select distinct vr.uid, vr.name
from validationrule vr
inner join expression le on vr.leftexpressionid=le.expressionid
inner join expression re on vr.rightexpressionid=re.expressionid
where le.expression ~ 'OuudMtJsh2z'
or re.expression  ~ 'OuudMtJsh2z'


-- DASHBOARDS

-- Visualizations ordered by count of data items

select v.uid as viz_uid, v.name as viz_name, count(vd.datadimensionitemid) as data_dim_item_count
from visualization v
inner join visualization_datadimensionitems vd on v.visualizationid = vd.visualizationid 
group by v.uid, v.name
order by data_dim_item_count desc
limit 100;

-- Dashboards ordered by count of data items in visualizations in dashboard items

select d.uid dashboard_uid, d.name as dashboard_name, count(vd.datadimensionitemid) as data_dim_item_count
from dashboard d
inner join dashboard_items dis on d.dashboardid = dis.dashboardid 
inner join dashboarditem di on dis.dashboarditemid = di.dashboarditemid 
inner join visualization v on di.visualizationid = v.visualizationid 
inner join visualization_datadimensionitems vd on v.visualizationid = vd.visualizationid 
group by d.uid, d.name
order by data_dim_item_count desc
limit 100;

-- (Write) Remove orphaned dashboard items

delete from dashboarditem di 
where di.dashboarditemid not in (
  select dashboarditemid from dashboard_items)
and di.dashboarditemid not in (
  select dashboarditemid from dashboarditem_reports)
and di.dashboarditemid not in (
  select dashboarditemid from dashboarditem_reporttables)
and di.dashboarditemid not in (
  select dashboarditemid from dashboarditem_resources)
and di.dashboarditemid not in (
  select dashboarditemid from dashboarditem_users);
  
  
-- DATA VALUES

-- Display data out of reasonable time range

select count(*)
from datavalue dv
where dv.periodid in (
  select pe.periodid
  from period pe
  where pe.startdate < '1960-01-01'
  or pe.enddate > '2020-01-01');

-- (Write) Delete all data values for category combo

delete from datavalue where categoryoptioncomboid in (
select coc.categoryoptioncomboid from categoryoptioncombo coc
inner join categorycombos_optioncombos co on coc.categoryoptioncomboid=co.categoryoptioncomboid
inner join categorycombo cc on co.categorycomboid=cc.categorycomboid
where cc.uid='iO1SPIBYKuJ');

-- (Write) Delete all data values for an attribute category option

delete from datavalue dv
where dv.attributeoptioncomboid in (
  select coc.categoryoptioncomboid from categoryoptioncombo coc
  inner join categoryoptioncombos_categoryoptions coo on coc.categoryoptioncomboid=coo.categoryoptioncomboid
  inner join dataelementcategoryoption co on coo.categoryoptionid=co.categoryoptionid
  where co.uid='LPeJEUjotaB');

-- (Write) Delete all data values for a data set
  
delete from datavalue dv
where dv.dataelementid in (
  select dse.dataelementid
  from datasetelement dse
  inner join dataset ds on dse.datasetid=ds.datasetid
  where ds.uid='j38YW1Am7he');

-- (Write) Delete zero data values

delete from datavalue where value in ('0', '0.0', '0.00');

-- (Write) Prune deleted data values

delete from datavalue where deleted is true;

-- Data value exploded view

select de.name as de_name, de.uid as de_uid, de.code as de_code, 
pe.startdate as pe_start, pe.enddate as pe_end, ps.iso as period_isoname, pt.name as pt_name, 
ou.name as ou_name, ou.uid as ou_uid, ou.code as ou_code, ou.hierarchylevel as ou_level,
coc.name as coc_name, coc.uid as coc_uid, coc.code as coc_code,
aoc.name as aoc_name, aoc.uid as aoc_uid, aoc.code as aoc_code, dv.value as value
from datavalue dv
inner join dataelement de on dv.dataelementid=de.dataelementid
inner join period pe on dv.periodid=pe.periodid
inner join periodtype pt on pe.periodtypeid=pt.periodtypeid
left join _periodstructure ps on pe.periodid=ps.periodid 
inner join organisationunit ou on dv.sourceid=ou.organisationunitid
inner join categoryoptioncombo coc on dv.categoryoptioncomboid=coc.categoryoptioncomboid
inner join categoryoptioncombo aoc on dv.attributeoptioncomboid=aoc.categoryoptioncomboid;

-- Data values created by day

select dv.created::date as d_day, count(*) as d_count
from datavalue dv
where dv.lastupdated >= '2018-08-1'
group by d_day
order by d_day desc;

-- Data values created by day and hour

select dv.created::date as d_day, extract(hour from dv.lastupdated) as d_hour, count(*) as d_count
from datavalue dv
where dv.lastupdated >= '2018-08-1'
group by d_day, d_hour
order by d_day desc, d_hour desc;

-- Data values created by year and month

select extract(year from dv.created)::integer as yr, extract(month from dv.created)::integer as mo, count(*)
from datavalue dv
group by yr, mo
order by yr, mo;

-- Data values since date

select count(*) as d_count
from datavalue dv
where dv.lastupdated >= '2018-10-01';

-- Data value count by period

select ps.iso, count(ps.iso)
from datavalue dv
inner join "_periodstructure" ps on (dv.periodid=ps.periodid)
group by ps.iso
order by ps.iso asc;

-- Get count of data values by year and month

select extract(year from pe.startdate)::integer as yr, extract(month from pe.startdate)::integer as mo, count(*)
from datavalue dv
inner join period pe on dv.periodid=pe.periodid
group by yr, mo
order by yr, mo;

-- Get count of data values by year

select extract(year from pe.startdate)::integer as yr, count(*)
from datavalue dv
inner join period pe on dv.periodid=pe.periodid
group by yr
order by yr;

-- Get count of datavalues by data element

select de.name as de, count(*) as c
from datavalue dv
inner join dataelement de on dv.dataelementid=dv.dataelementid
group by de
order by c;

-- Drop and recreate foreign keys on data values for faster delete operations

alter table datavalue drop constraint fk_datavalue_attributeoptioncomboid;
alter table datavalue drop constraint fk_datavalue_categoryoptioncomboid;
alter table datavalue drop constraint fk_datavalue_dataelementid;
alter table datavalue drop constraint fk_datavalue_organisationunitid;
alter table datavalue drop constraint fk_datavalue_periodid;

alter table datavalue add constraint fk_datavalue_attributeoptioncomboid foreign key (attributeoptioncomboid) references categoryoptioncombo(categoryoptioncomboid);
alter table datavalue add constraint fk_datavalue_categoryoptioncomboid foreign key (categoryoptioncomboid) references categoryoptioncombo(categoryoptioncomboid);
alter table datavalue add constraint fk_datavalue_dataelementid foreign key (dataelementid) references dataelement(dataelementid);
alter table datavalue add constraint fk_datavalue_organisationunitid foreign key (sourceid) references organisationunit(organisationunitid);
alter table datavalue add constraint fk_datavalue_periodid foreign key (periodid) references period(periodid);


-- EVENTS

-- Display events out of reasonable time range

select count(*)
from programstageinstance psi
where psi.executiondate < '1960-01-01'
or psi.executiondate > '2023-01-01';

-- Delete events out of reasonable time range

delete from programstageinstance psi
where psi.executiondate < '1960-01-01'
or psi.executiondate > '2020-01-01';

-- Get count of events by year and month by executiondate

select extract(year from psi.executiondate)::integer as yr, extract(month from psi.executiondate)::integer as mo, count(*)
from programstageinstance psi
group by yr, mo
order by yr, mo;

-- Get counts of events by year by executiondate

select extract(year from psi.executiondate)::integer as yr, count(*)
from programstageinstance psi
group by yr
order by yr;

-- Get count of data elements per program

select pr.name, count(psd.uid)
from program pr
inner join programstage ps on pr.programid=ps.programid
inner join programstagedataelement psd on ps.programstageid=psd.programstageid
group by pr.name;

-- Get count of events per program (deleted false)

select p.uid as program_uid, p.name as program_name, count(*) as event_count
from programstageinstance psi
inner join programinstance pi on psi.programinstanceid = pi.programinstanceid 
inner join program p on pi.programid = p.programid
where psi.deleted = false
group by p.uid, p.name
order by p.name;

-- Get count of event audit values per program (deleted false)

select p.uid as program_uid, p.name as program_name, count(*) as audit_value_count
from trackedentitydatavalueaudit tedva
inner join programstageinstance psi on tedva.programstageinstanceid = psi.programstageinstanceid 
inner join programinstance pi on psi.programinstanceid = pi.programinstanceid 
inner join program p on pi.programid = p.programid
where psi.deleted = false
group by p.uid, p.name
order by p.name;

-- (Write) Generate random coordinates based on org unit location for events

update programstageinstance psi
set longitude = (
  select ( cast( regexp_replace( coordinates, '\[(-?\d+\.?\d*)[,](-?\d+\.?\d*)\]', '\1' ) as double precision ) + ( random() / 10 ) )
  from organisationunit ou
  where psi.organisationunitid=ou.organisationunitid ),
latitude = (
  select ( cast( regexp_replace( coordinates, '\[(-?\d+\.?\d*)[,](-?\d+\.?\d*)\]', '\2' ) as double precision ) + ( random() / 10 ) )
  from organisationunit ou
  where psi.organisationunitid=ou.organisationunitid );

-- (Write) Delete data values and events for a program

delete from trackedentitydatavalueaudit dv
where dv.programstageinstanceid in (
  select psi.programstageinstanceid
  from programstageinstance psi
  inner join programinstance pi on psi.programinstanceid=psi.programinstanceid
  inner join program pr on pi.programid=pr.programid
  where pr.uid = 'bMcwwoVnbSR');
  
delete from programstageinstance psi
where psi.programinstanceid in (
  select pi.programinstanceid
  from programinstance pi
  inner join program pr on pi.programid=pr.programid
  where pr.uid = 'bMcwwoVnbSR');
