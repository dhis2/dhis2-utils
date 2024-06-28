
-- Contains various integrity checks as SQL statements for the category related tables, each should ideally return no rows

-- Get overview of category combo > category > category option structure

select 
  substring(cc.name,0,100) as category_combo, 
  substring(c.name,0,60) as category, 
  substring(string_agg(substring(co.name,0,40), ' | ' order by co.name),0,130) as category_option,
  count(cocco.categoryoptioncomboid) as coc_count
from categorycombo cc
inner join categorycombos_categories ccc on cc.categorycomboid = ccc.categorycomboid 
inner join dataelementcategory c on ccc.categoryid = c.categoryid 
inner join categories_categoryoptions cco on c.categoryid = cco.categoryid 
inner join dataelementcategoryoption co on cco.categoryoptionid = co.categoryoptionid
inner join categoryoptioncombos_categoryoptions cocco on co.categoryoptionid = cocco.categoryoptionid
group by category_combo, category
order by category_combo, category;

-- Get category option combos without category options

select * from categoryoptioncombo where categoryoptioncomboid not in (select distinct categoryoptioncomboid from categoryoptioncombos_categoryoptions);

-- Get category option combos without category combo

select * from categoryoptioncombo where categoryoptioncomboid not in (select distinct categoryoptioncomboid from categorycombos_optioncombos);

-- Get category option combos without category options or category combos

select * from categoryoptioncombo
where categoryoptioncomboid not in (select distinct categoryoptioncomboid from categoryoptioncombos_categoryoptions)
and categoryoptioncomboid not in (select distinct categoryoptioncomboid from categorycombos_optioncombos);

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

-- Get category option combos whose name is blank or null

select * from categoryoptioncombo where name ='' or name is null;

-- Get category combos with categories which share the same category options

select cc.name as cc_name, co.name as co_name from categorycombo cc 
inner join categorycombos_categories ccc on cc.categorycomboid=ccc.categorycomboid
inner join categories_categoryoptions cco on ccc.categoryid=cco.categoryid
inner join dataelementcategoryoption co on cco.categoryoptionid=co.categoryoptionid
group by cc_name, co_name having count(*) > 1;

-- Get category combinations without data elements or data sets

select * from categorycombo where categorycomboid not in (select distinct categorycomboid from dataelement);

-- Get category option combos which have disjoint associations with category options within categories

-- This normally results from altering the category options within a category after the category combo has been created

WITH foo as (
SELECT DISTINCT a.categorycomboid, b.categoryoptionid from categorycombos_optioncombos a
INNER JOIN  categoryoptioncombos_categoryoptions  b on a.categoryoptioncomboid= b.categoryoptioncomboid
EXCEPT
SELECT a.categorycomboid,b.categoryoptionid from categorycombos_categories a
INNER JOIN categories_categoryoptions b on a.categoryid = b.categoryid )
SELECT y.uid as catcombo_uid,z.uid as catoption_uid,y.name,z.name from foo x
INNER JOIN categorycombo y on x.categorycomboid = y.categorycomboid
INNER JOIN dataelementcategoryoption z on x. categoryoptionid = z. categoryoptionid;

-- Get category option combos whose cardnality differs from the theoretical cardnality as defined by the number of categories

WITH baz as (
SELECT foo.categorycomboid,foo.categoryoptioncomboid,foo.actual_cardnality,bar.theoretical_cardnality FROM (
SELECT b.categorycomboid,a.categoryoptioncomboid, COUNT(*) as actual_cardnality FROM categoryoptioncombos_categoryoptions a
INNER JOIN categorycombos_optioncombos b on a.categoryoptioncomboid = b.categoryoptioncomboid
GROUP BY b.categorycomboid,a.categoryoptioncomboid ) as foo
INNER JOIN 
(SELECT categorycomboid,COUNT(*) as theoretical_cardnality FROM categorycombos_categories
  GROUP BY categorycomboid) bar on foo.categorycomboid = bar.categorycomboid
WHERE foo.actual_cardnality != bar.theoretical_cardnality )
SELECT x.uid as catcombo_uid,y.uid as coc_uid,x.name as catcombo_name,y.name as coc_name,
baz.actual_cardnality,baz.theoretical_cardnality 
FROM baz
INNER JOIN categorycombo x on baz.categorycomboid = x.categorycomboid
INNER JOIN categoryoptioncombo y on baz.categoryoptioncomboid = y.categoryoptioncomboid;

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


-- WRITE BE CAREFUL

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


