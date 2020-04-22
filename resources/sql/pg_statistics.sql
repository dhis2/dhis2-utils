

-- Approximate count of rows in analytics tables

select relname as table_name, reltuples::bigint as approximate_row_count 
from pg_class 
where relname like 'analytics_%'
order by approximate_row_count desc;

-- Approximate count of rows in raw data and event

select relname as table_name, reltuples::bigint as approximate_row_count 
from pg_class 
where relname in ('datavalue', 'trackedentityinstance', 'programstageinstance', 'trackedentitydatavalue')
order by approximate_row_count desc;
