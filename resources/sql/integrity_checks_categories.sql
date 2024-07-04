
--
-- Contains various integrity checks as SQL statements for the category related tables, each should ideally return no rows
--

--
-- Category option combos
--

-- Create support table for category option combos with data values

create table _tmp_coc_with_dv (categoryoptioncomboid int8);
insert into _tmp_coc_with_dv (categoryoptioncomboid) 
select distinct dv.categoryoptioncomboid from datavalue dv;

-- Get category option combos without category options

select * from categoryoptioncombo 
where categoryoptioncomboid not in (
  select categoryoptioncomboid from categoryoptioncombos_categoryoptions);

-- Get category option combos without category combo

select * from categoryoptioncombo 
where categoryoptioncomboid not in (
  select categoryoptioncomboid from categorycombos_optioncombos);
x|
-- Get category option combos without category options or category combos

select * from categoryoptioncombo
where categoryoptioncomboid not in (
  select categoryoptioncomboid from categoryoptioncombos_categoryoptions)
and categoryoptioncomboid not in (
  select categoryoptioncomboid from categorycombos_optioncombos);

-- Category option combos members of more than one category combo

select categoryoptioncomboid, count(categoryoptioncomboid) as count from categorycombos_optioncombos 
group by categoryoptioncomboid having count(categoryoptioncomboid) > 1;

-- Get additional default option combos 1

select * from categoryoptioncombo coc 
inner join categorycombos_optioncombos ccoc on coc.categoryoptioncomboid=ccoc.categoryoptioncomboid 
inner join categorycombo cc on ccoc.categorycomboid=cc.categorycomboid 
where cc.name = 'default' offset 1;

-- Get additional default option combos 2

select * from categoryoptioncombo coc 
inner join categoryoptioncombos_categoryoptions cocco on coc.categoryoptioncomboid=cocco.categoryoptioncomboid 
inner join dataelementcategoryoption co on cocco.categoryoptionid=co.categoryoptionid 
where co.name = 'default' offset 1;

-- Get category option combos without data values (not an error)

select * from categoryoptioncombo 
where categoryoptioncomboid not in (
  select categoryoptioncomboid from datavalue);

--
-- Category options
--

-- Get category options without category option combos (be careful when deleting from categories_categoryoptions to avoid missing indexes)

select * from dataelementcategoryoption 
where categoryoptionid not in (
  select categoryoptionid from categoryoptioncombos_categoryoptions);

-- Get category options without categories

select * from dataelementcategoryoption 
where categoryoptionid not in (
  select categoryoptionid from categories_categoryoptions);

-- Get category options without categories and category option combos

select * from dataelementcategoryoption 
where categoryoptionid not in (
  select categoryoptionid from categories_categoryoptions)
and categoryoptionid not in (
  select categoryoptionid from categoryoptioncombos_categoryoptions);

-- Get category options with more than one membership for a category 

select categoryid, categoryoptionid, count(*) from categories_categoryoptions 
group by categoryid, categoryoptionid having count(*) > 1;

-- Get category options with count of memberships in categories

select co.categoryoptionid, co.name, (select count(categoryoptionid) 
from categories_categoryoptions 
where categoryoptionid=co.categoryoptionid ) as categorycount from dataelementcategoryoption co 
order by categorycount desc;

--
-- Categories
--

-- Get categories without category options

select * from dataelementcategory 
where categoryid not in (
  select categoryid from categories_categoryoptions);

-- Get categories without category combos

select * from dataelementcategory 
where categoryid not in (
  select categoryid from categorycombos_categories);

-- Get categories without category combos and category options

select * from dataelementcategory 
where categoryid not in (
  select categoryid from categorycombos_categories)
and categoryid not in (
  select categoryid from categories_categoryoptions);

-- Get categories without category combos and category option combos associated with data values

select c.categoryid, c.uid, c.name
from dataelementcategory c
where c.categoryid not in (
  select ccc.categoryid
  from categorycombos_categories ccc
  where ccc.categoryid = c.categoryid)
and c.categoryid not in (
  select cco.categoryid 
  from categories_categoryoptions cco
  inner join categoryoptioncombos_categoryoptions cocco on cco.categoryoptionid = cocco.categoryoptionid
  inner join _tmp_coc_with_dv cocdv on cocco.categoryoptioncomboid = cocdv.categoryoptioncomboid);

-- Get categories with only one category option

with category_cateory_option_count as (
  select c.categoryid, c.uid, c.name, (
    select count(*)
    from categories_categoryoptions cco
    where cco.categoryid = c.categoryid) as co_count
    from dataelementcategory c)
select c.uid, c.name
from category_cateory_option_count c
where c.co_count = 1;

-- Get categories with more than one membership for a category combination

select categorycomboid, categoryid, count(*) from categorycombos_categories 
group by categorycomboid, categoryid having count(*) > 1;

--
-- Category combos
--

-- Get category combos without categories

select * from categorycombo 
where categorycomboid not in (
  select categorycomboid from categorycombos_categories);

-- Get category combos without category option combos

select * from categorycombo 
where categorycomboid not in (
  select categorycomboid from categorycombos_optioncombos);

-- Get category combos not used in data elements, data sets or programs

select cc.categorycomboid, cc.uid, cc.name 
from categorycombo cc
where not exists (
  select 1
  from dataelement de
  where de.categorycomboid = cc.categorycomboid)
and not exists (
  select 1
  from dataset ds
  where ds.categorycomboid = cc.categorycomboid)
and not exists (
  select 1
  from program p
  where p.categorycomboid = cc.categorycomboid);

-- Get category option combos without data values (not an error)

select * from categoryoptioncombo 
where categoryoptioncomboid not in (
  select categoryoptioncomboid from datavalue);

-- Get category combos with categories which share the same category options

select cc.name as cc_name, co.name as co_name from categorycombo cc 
inner join categorycombos_categories ccc on cc.categorycomboid=ccc.categorycomboid
inner join categories_categoryoptions cco on ccc.categoryid=cco.categoryid
inner join dataelementcategoryoption co on cco.categoryoptionid=co.categoryoptionid
group by cc_name, co_name having count(*) > 1;

-- Get category combos without data elements or data sets

select * from categorycombo 
where categorycomboid not in (
  select categorycomboid from dataelement);

-- Get data values where category option combo is not part of category combo of data element

select de.name as dataelement_name, pes.iso, ou.name as orgunit_name, cocn.categoryoptioncomboname, dv.value
from datavalue dv
inner join dataelement de on dv.dataelementid=de.dataelementid
inner join _periodstructure pes on dv.periodid=pes.periodid
inner join organisationunit ou on dv.sourceid=ou.organisationunitid
inner join _categoryoptioncomboname cocn on dv.categoryoptioncomboid=cocn.categoryoptioncomboid
where dv.categoryoptioncomboid not in (
  select ccoc2.categoryoptioncomboid
  from categorycombos_optioncombos ccoc2
  where ccoc2.categorycomboid=de.categorycomboid)
limit 10000;

-- Get data values where attribute option combo is not part of the category combo of data set

select des.dataelementname, ds.name as dataset_name, pes.iso, ou.name as orgunit_name, cocn.categoryoptioncomboname, dv.value
from datavalue dv
inner join _dataelementstructure des on dv.dataelementid=des.dataelementid
inner join dataset ds on des.datasetid=ds.datasetid
inner join _periodstructure pes on dv.periodid=pes.periodid
inner join organisationunit ou on dv.sourceid=ou.organisationunitid
inner join _categoryoptioncomboname cocn on dv.attributeoptioncomboid=cocn.categoryoptioncomboid
where dv.attributeoptioncomboid not in (
  select ccoc2.categoryoptioncomboid
  from categorycombos_optioncombos ccoc2
  where ccoc2.categorycomboid=ds.categorycomboid)
limit 10000;

-- Get category option combos from data values which are not part of the category combo of the data element

select distinct de.name as data_element, dv.dataelementid, de_cc.name as data_element_category_combo, oc_cc.name as option_combo_category_combo, con.categoryoptioncomboname, dv.categoryoptioncomboid
from datavalue dv
left join dataelement de on dv.dataelementid=de.dataelementid
left join categorycombo de_cc on de.categorycomboid=de_cc.categorycomboid
inner join categorycombos_optioncombos cc_oc on dv.categoryoptioncomboid=cc_oc.categoryoptioncomboid
left join categorycombo oc_cc on cc_oc.categorycomboid=oc_cc.categorycomboid
left join _categoryoptioncomboname con on dv.categoryoptioncomboid=con.categoryoptioncomboid
where not exists (
  select 1 from _dataelementcategoryoptioncombo dc
  where dc.dataelementid=dv.dataelementid
  and dc.categoryoptioncomboid=dv.categoryoptioncomboid);

--
-- WRITE STATEMENTS BE CAREFUL
--

-- Repair missing link row between default category and default category option

insert into categories_categoryoptions(categoryid, categoryoptionid, sort_order)
select categoryid, categoryoptionid, 1 from
(select categoryid from dataelementcategory where name = 'default') as categoryid,
(select categoryoptionid from dataelementcategoryoption where name = 'default') as categoryoptionid;

-- Repair missing link row between default category combo and default category

insert into categorycombos_categories(categorycomboid, categoryid, sort_order)
select categorycomboid, categoryid, 1 from
(select categorycomboid from categorycombo where name = 'default') as categorycomboid,
(select categoryid from dataelementcategory where name = 'default') as categoryid;

-- Repair missing link row between default category option and default category option combo

insert into categoryoptioncombos_categoryoptions(categoryoptionid, categoryoptioncomboid)
select categoryoptionid, categoryoptioncomboid from
(select categoryoptionid from dataelementcategoryoption where name = 'default') as categoryoptionid,
(select categoryoptioncomboid from categoryoptioncombo where name = 'default') as categoryoptioncomboid;
