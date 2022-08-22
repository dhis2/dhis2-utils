--generating  buffer periods from the future/current  year to be used as a buffering period 
--the buffering periods will be the same periodId for the future/current year with an extra two digits from  the buffering year

Drop  function if EXISTS generate_buffer_period_from_current_period( );
create or replace function generate_buffer_period_from_current_period( )
returns table (
	p_id 	BIGINT,
	p_type  int,
 	p_start date,
	p_end   date,
	p_old_startdate date,
	p_old_enddate date,
	  p_name2  varchar
--	p_month_no int
) 
language plpgsql
as $$
declare 
    var_r record;
		var_r_r record;
	   min_p_year int;
     min_p_datavalue_year int;
      rec record;  
begin
---this part of the query will return a minimum year which has data values 
   min_p_year := (select date_part('year',min(pp.startdate))-1 as bufferyear_no_p from period pp);
   min_p_datavalue_year := ( select date_part('year',min(pp.startdate))-1 as bufferyear_no_pv 
	 from datavalue dv
   LEFT JOIN period pp on dv.periodid = pp.periodid
   LEFT JOIN periodtype pt on pp.periodtypeid = pt.periodtypeid
	 );

  IF min_p_year !=   min_p_datavalue_year  THEN
  raise notice 'empty peroid will be  deleted from peroid table';
	
	FOR rec IN SELECT periodid from period where date_part('year',startdate)<=min_p_datavalue_year 
    LOOP
        DELETE from period where periodid=rec.periodid;
				raise notice  'peroidid deleted  (%)',rec.periodid;
        -- return NEXT ; -- return current row of SELECT
    END LOOP;
	
	else 
	raise notice  'peroid for year   (%) will be populated',min_p_datavalue_year;
	end if;
	
for var_r in(

with temp_buffer_year as 
( select date_part('year',min(pp.startdate))-1 as bufferyear_no from period pp),
current_year as
 (
select pp.periodid as pid,pp.startdate as Sdate,pp.enddate as Edate,pp.periodtypeid as newperiodtypeid ,pt.name as periodType ,
pp.periodtypeid, pp.startdate,  concat(pp.periodid,pp.periodtypeid) as newpid
from period pp
INNER JOIN periodtype pt ON pp.periodtypeid = pt.periodtypeid
 where date_part('year',startDate)= date_part('year',now())--NULLIF(future_year, 2025)
 order by pp.periodtypeid, pp.startdate
 
 ),
---this part of the query will return a list of periods of the buffering year
 Buffer_peroid as (
 select sdate,	Edate,int8( concat(pid,right(cast (bufferyear_no as text),2)) ) as new_buffer_Peroidid,newperiodtypeid as new_buffer_periodtypeid,
cast (concat(cast (bufferyear_no as text),right(cast (Sdate as text),6)) as date) as  newbfSdate ,
cast(concat(cast (bufferyear_no as text),right(cast (Edate as text),6)) as date) as    newbfEdate ,periodType
from temp_buffer_year,current_year

---this part of the query will fix the start and end date of the periods in the buffering year
), new_Buffer_peroid as(
 select new_buffer_Peroidid,new_buffer_periodtypeid,Sdate,
 case 
 
	--WHEN periodType= 'Weekly' THEN newbfSdate + 1 - cast(abs(extract(isodow from newbfSdate)) as int)  
	WHEN periodType = 'WeeklyWednesday' THEN newbfSdate + 3 - cast(abs(extract(isodow from newbfSdate)) as int)
	WHEN periodType= 'WeeklyThursday' THEN newbfSdate + 4 - cast(abs(extract(isodow from newbfSdate)) as int)            
	WHEN periodType = 'WeeklySaturday' THEN newbfSdate + 6 - cast(abs(extract(isodow from newbfSdate)) as int) 
	WHEN periodType = 'WeeklySunday' THEN newbfSdate + 7 - cast(abs(extract(isodow from newbfSdate)) as int) 
	WHEN periodType = 'Daily' THEN newbfSdate 
	WHEN periodType = 'Monthly' THEN newbfSdate 
	else newbfSdate 
	END as new_startdate  ,	

 case 

	WHEN periodType= '%Weekly%' THEN  to_char(newbfSdate + interval '6 days', 'YYYY-MM-DD')::date
	WHEN periodType = 'Monthly' THEN (newbfSdate + (interval '1 month') - (interval '1 day'))::date
	WHEN periodType= 'BiMonthly' THEN (newbfSdate + (interval '2 months') - (interval '1 day'))::date           
	WHEN periodType = 'SixMonthly%' THEN (newbfSdate + (interval '6 months') - (interval '1 day'))::date
	else newbfEdate
			END as new_enddate ,
			Sdate as startdate_old,
			Edate as enddate_old,
			periodType as ptname
from Buffer_peroid )
select * from new_Buffer_peroid

	)



 loop  
    p_id  := var_r.new_buffer_Peroidid ; 
		p_type := var_r.new_buffer_periodtypeid;
	 		p_start  := var_r.new_startdate;
		p_end  := var_r.new_enddate  ;
			p_old_startdate :=var_r.startdate_old;
			p_old_enddate :=var_r.enddate_old;
			  p_name2 :=var_r.ptname;
	--	p_month_no  := var_r.month_no;
         return next;
	end loop ;
	

end; $$ ;

INSERT into period select  p_id,	p_type,p_start,p_end from generate_buffer_period_from_current_period();
--select * from generate_buffer_period_from_current_period();