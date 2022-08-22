---- Move all buffer  data to the current period
-- to be used by corn each peroid 
CREATE FUNCTION move_buffering_to_current (period_type text) RETURNS boolean
    LANGUAGE plpgsql
AS
$$
DECLARE
BEGIN

with buffer_year_peroid as (
select  left(cast (periodid as text),-2)::BIGINT as old_peroid,periodid,periodtypeid,startdate,enddate, date_part('year',startdate) as buffer_year from period where date_part('year',startdate) = (select date_part('year',min(pp.startdate))  from period pp) 
),

feature_year_peroid as (

select periodid::BIGINT as pp,periodtypeid,startdate,enddate from period where date_part('year',startdate)=date_part('year',now()) 
),
pre_update as( 

select old_peroid,bf_year.periodid as new_peroid,f_year.startdate as f_startdate,f_year.enddate as f_enddate ,bf_year.periodtypeid ,pp as feature_period,bf_year.startdate as bf_startdate ,bf_year.enddate as bf_enddate
from buffer_year_peroid bf_year 
JOIN feature_year_peroid f_year on f_year.pp=bf_year.old_peroid

),

dv2 as (

select dataelementid,sourceid,        categoryoptioncomboid,        attributeoptioncomboid,        value,  dv.periodid
from datavalue dv
INNER JOIN pre_update on  dv.periodid=pre_update.new_peroid
)

--select * from pre_update

update datavalue dv
set periodid=pre_update.feature_period
from pre_update
inner join dv2 on dv2.periodid=pre_update.new_peroid
LEFT JOIN periodtype pt on pre_update.periodtypeid = pt.periodtypeid
where dv.periodid=pre_update.new_peroid
and pre_update.f_startdate ::date  <= now() :: date
and dv2.dataelementid=dv.dataelementid 
and dv2.sourceid=dv.sourceid
and dv2.categoryoptioncomboid=dv.categoryoptioncomboid
and dv2.attributeoptioncomboid=dv.attributeoptioncomboid
and dv2.value=dv.value 
and pt.name = period_type;
    RETURN TRUE;
END
$$;
-- passing peroid type name to the function  monthly , Daily, weekly 
--select move_buffering_to_current('monthly');