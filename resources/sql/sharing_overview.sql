select name,uid,type, ug, ug_name from (

select distinct a.name as name, a.uid as uid, 'categoryoption' as type, ug.uid as ug, ug.name as ug_name from dataelementcategoryoption a 
inner join dataelementcategoryoptionusergroupaccesses b on a.categoryoptionid=b.categoryoptionid
inner join usergroupaccess uga on b.usergroupaccessid=uga.usergroupaccessid
inner join usergroup ug on uga.usergroupid=ug.usergroupid

union all

select distinct a.name as name, a.uid as uid, 'category' as type, ug.uid as ug, ug.name as ug_name from dataelementcategory a 
inner join dataelementcategoryusergroupaccesses b on a.categoryid=b.categoryid
inner join usergroupaccess uga on b.usergroupaccessid=uga.usergroupaccessid
inner join usergroup ug on uga.usergroupid=ug.usergroupid

union all

select distinct a.name as name, a.uid as uid, 'categorycombo' as type, ug.uid as ug, ug.name as ug_name from categorycombo a 
inner join categorycombousergroupaccesses b on a.categorycomboid=b.categorycomboid
inner join usergroupaccess uga on b.usergroupaccessid=uga.usergroupaccessid
inner join usergroup ug on uga.usergroupid=ug.usergroupid

union all

select distinct a.name as name, a.uid as uid, 'categoryoptiongroup' as type, ug.uid as ug, ug.name as ug_name from categoryoptiongroup a 
inner join categoryoptiongroupusergroupaccesses b on a.categoryoptiongroupid=b.categoryoptiongroupid
inner join usergroupaccess uga on b.usergroupaccessid=uga.usergroupaccessid
inner join usergroup ug on uga.usergroupid=ug.usergroupid 

union all

select distinct a.name as name, a.uid as uid, 'categoryoptiongroupset' as type, ug.uid as ug, ug.name as ug_name from categoryoptiongroupset a 
inner join categoryoptiongroupsetusergroupaccesses b on a.categoryoptiongroupsetid=b.categoryoptiongroupsetid
inner join usergroupaccess uga on b.usergroupaccessid=uga.usergroupaccessid
inner join usergroup ug on uga.usergroupid=ug.usergroupid 

union all

select distinct a.name as name, a.uid as uid, 'dataelement' as type, ug.uid as ug, ug.name as ug_name from dataelement a 
inner join dataelementusergroupaccesses b on a.dataelementid=b.dataelementid
inner join usergroupaccess uga on b.usergroupaccessid=uga.usergroupaccessid
inner join usergroup ug on uga.usergroupid=ug.usergroupid 

union all

select distinct a.name as name, a.uid as uid, 'dataelementgroup' as type, ug.uid as ug, ug.name as ug_name from dataelementgroup a 
inner join dataelementgroupusergroupaccesses b on a.dataelementgroupid=b.dataelementgroupid
inner join usergroupaccess uga on b.usergroupaccessid=uga.usergroupaccessid
inner join usergroup ug on uga.usergroupid=ug.usergroupid 

union all

select distinct a.name as name, a.uid as uid, 'dataelementgroupset' as type, ug.uid as ug, ug.name as ug_name from dataelementgroupset a 
inner join dataelementgroupsetusergroupaccesses b on a.dataelementgroupsetid=b.dataelementgroupsetid
inner join usergroupaccess uga on b.usergroupaccessid=uga.usergroupaccessid
inner join usergroup ug on uga.usergroupid=ug.usergroupid 

union all

select distinct a.name as name, a.uid as uid, 'dataset' as type, ug.uid as ug, ug.name as ug_name from dataset a 
inner join datasetusergroupaccesses b on a.datasetid=b.datasetid
inner join usergroupaccess uga on b.usergroupaccessid=uga.usergroupaccessid
inner join usergroup ug on uga.usergroupid=ug.usergroupid 

union all

select distinct a.name as name, a.uid as uid, 'indicator' as type, ug.uid as ug, ug.name as ug_name from indicator a 
inner join indicatorusergroupaccesses b on a.indicatorid=b.indicatorid
inner join usergroupaccess uga on b.usergroupaccessid=uga.usergroupaccessid
inner join usergroup ug on uga.usergroupid=ug.usergroupid 

union all

select distinct a.name as name, a.uid as uid, 'indicatorgroup' as type, ug.uid as ug, ug.name as ug_name from indicatorgroup a 
inner join indicatorgroupusergroupaccesses b on a.indicatorgroupid=b.indicatorgroupid
inner join usergroupaccess uga on b.usergroupaccessid=uga.usergroupaccessid
inner join usergroup ug on uga.usergroupid=ug.usergroupid 

union all

select distinct a.name as name, a.uid as uid, 'indicatorgroupset' as type, ug.uid as ug, ug.name as ug_name from indicatorgroupset a 
inner join indicatorgroupsetusergroupaccesses b on a.indicatorgroupsetid=b.indicatorgroupsetid
inner join usergroupaccess uga on b.usergroupaccessid=uga.usergroupaccessid
inner join usergroup ug on uga.usergroupid=ug.usergroupid 

union all

select distinct a.name as name, a.uid as uid, 'orgunitgroup' as type, ug.uid as ug, ug.name as ug_name from orgunitgroup a 
inner join orgunitgroupusergroupaccesses b on a.orgunitgroupid=b.orgunitgroupid
inner join usergroupaccess uga on b.usergroupaccessid=uga.usergroupaccessid
inner join usergroup ug on uga.usergroupid=ug.usergroupid 

union all

select distinct a.name as name, a.uid as uid, 'orgunitgroupset' as type, ug.uid as ug, ug.name as ug_name from orgunitgroupset a 
inner join orgunitgroupsetusergroupaccesses b on a.orgunitgroupsetid=b.orgunitgroupsetid
inner join usergroupaccess uga on b.usergroupaccessid=uga.usergroupaccessid
inner join usergroup ug on uga.usergroupid=ug.usergroupid 

) as items where ug='FDy0VsGjccX';

