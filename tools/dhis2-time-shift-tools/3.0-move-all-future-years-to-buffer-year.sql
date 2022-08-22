-- Move all feature data to the buffer period
CREATE FUNCTION move_current_buffering () RETURNS boolean
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

select old_peroid,bf_year.periodid as new_peroid,f_year.startdate as f_startdate,f_year.enddate as f_enddate ,bf_year.periodtypeid ,pp ,bf_year.startdate as bf_startdate ,bf_year.enddate as bf_enddate
from buffer_year_peroid bf_year 
JOIN feature_year_peroid f_year on f_year.pp=bf_year.old_peroid

),

dv2 as (

select dataelementid,sourceid, categoryoptioncomboid,        attributeoptioncomboid,        value,  dv.periodid
from datavalue dv
INNER JOIN pre_update on  dv.periodid=pre_update.pp
)


update datavalue dv
set periodid=pre_update.new_peroid
from pre_update
inner join dv2 on dv2.periodid=pre_update.old_peroid 
where dv.periodid=pre_update.old_peroid 
--and pre_update.f_startdate>= now() :: date
and dv2.dataelementid=dv.dataelementid 
and dv2.sourceid=dv.sourceid
and dv2.categoryoptioncomboid=dv.categoryoptioncomboid
and dv2.attributeoptioncomboid=dv.attributeoptioncomboid
and dv2.value=dv.value ;
   RETURN TRUE;
END
$$;

--select move_current_buffering ();