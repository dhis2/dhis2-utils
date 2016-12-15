
-- Get category option combos without category options

select * from categoryoptioncombo where categoryoptioncomboid not in (select distinct categoryoptioncomboid from categoryoptioncombos_categoryoptions);

-- Get category option combos without category combo

select * from categoryoptioncombo where categoryoptioncomboid not in (select distinct categoryoptioncomboid from categorycombos_optioncombos);

-- Get category options without category option combos (be careful when deleting from categories_categoryoptions to avoid missing indexes)

select * from dataelementcategoryoption where categoryoptionid not in (select distinct categoryoptionid from categoryoptioncombos_categoryoptions);

-- Get catetegory options without categories

select * from dataelementcategoryoption where categoryoptionid not in (select distinct categoryoptionid from categories_categoryoptions);

-- Get categories without category options

select * from dataelementcategory where categoryid not in (select distinct categoryid from categories_categoryoptions);

-- Get categories without category combos (not an error but could be removed)

select * from dataelementcategory where categoryid not in (select distinct categoryid from categorycombos_categories);

-- Get category combos without categories

select * from categorycombo where categorycomboid not in (select distinct categorycomboid from categorycombos_categories);

-- Get category options with more than one membership for a category 

select categoryid, categoryoptionid, count(*) from categories_categoryoptions group by categoryid, categoryoptionid having count(*) > 1;

-- Get category combos without category option combos

select * from categorycombo where categorycomboid not in (select distinct categorycomboid from categorycombos_optioncombos);

-- Get categories with more than one membership for a category combination

select categorycomboid, categoryid, count(*) from categorycombos_categories group by categorycomboid, categoryid having count(*) > 1;

-- Category option combos members of more than one category combo

select categoryoptioncomboid, count(categoryoptioncomboid) as count from categorycombos_optioncombos group by categoryoptioncomboid having count(categoryoptioncomboid) > 1;

-- Get additional default option combos 1

select * from categoryoptioncombo coc inner join categorycombos_optioncombos ccoc on coc.categoryoptioncomboid=ccoc.categoryoptioncomboid inner join categorycombo cc on ccoc.categorycomboid=cc.categorycomboid where cc.name = 'default' offset 1;

-- Get additional default option combos 2

select * from categoryoptioncombo coc inner join categoryoptioncombos_categoryoptions cocco on coc.categoryoptioncomboid=cocco.categoryoptioncomboid inner join dataelementcategoryoption co on cocco.categoryoptionid=co.categoryoptionid where co.name = 'default' offset 1;

-- Get category options with count of memberships in categories

select co.categoryoptionid, co.name, (select count(categoryoptionid) from categories_categoryoptions where categoryoptionid=co.categoryoptionid ) as categorycount from dataelementcategoryoption co order by categorycount desc;

-- Get category option combos without data values (not an error)

select * from categoryoptioncombo where categoryoptioncomboid not in (select distinct categoryoptioncomboid from datavalue);

-- Get category combos with categories which share the same category options

select cc.name as cc_name, co.name as co_name from categorycombo cc 
inner join categorycombos_categories ccc on cc.categorycomboid=ccc.categorycomboid
inner join categories_categoryoptions cco on ccc.categoryid=cco.categoryid
inner join dataelementcategoryoption co on cco.categoryoptionid=co.categoryoptionid
group by cc_name, co_name having count(*) > 1;

-- Get category combinations without data elements or data sets

select * from categorycombo where categorycomboid not in (select distinct categorycomboid from dataelement);

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
  
-- Get category option combos not part of _categoryoptioncomboname resource table

select * from categoryoptioncombo coc
where coc.categoryoptioncomboid not in (
  select cocn.categoryoptioncomboid
  from _categoryoptioncomboname cocn);

-- Get category combo with no data elements

select cc.categorycomboid, cc.name from categorycombo cc where cc.categorycomboid not in (
select distinct categorycomboid from dataelement);


-- WRITE

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


