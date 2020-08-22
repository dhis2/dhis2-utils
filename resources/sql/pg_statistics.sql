
-- SIZE

-- Get size of all tables

select table_name, pg_size_pretty(pg_relation_size(quote_ident(table_name))) as table_size
from information_schema.tables
where table_schema = 'public'
order by pg_relation_size(quote_ident(table_name)) desc;


-- ANALYTICS

-- Approximate count of rows in analytics tables

select relname as table_name, reltuples::bigint as approximate_row_count 
from pg_class 
where relname like 'analytics_%'
order by approximate_row_count desc;

-- Approximate count of rows in raw data and event tables

select relname as table_name, reltuples::bigint as approximate_row_count 
from pg_class 
where relname in ('datavalue', 'trackedentityinstance', 'programstageinstance', 'trackedentitydatavalue')
order by approximate_row_count desc;

-- Approximate comparison between counts of raw data and analytics data

drop view if exists _raw_count;
drop view if exists _analytics_count;

create view _raw_count as (
  select extract(year from psi.executiondate)::integer as yr, count(*) as row_count
  from programstageinstance psi
  group by yr);

create view _analytics_count as (
  select (regexp_matches(relname,'^analytics_event_.*(\d{4}).*', 'g'))[1]::int as yr, sum(reltuples::bigint) as row_count 
  from pg_class 
  where relname like 'analytics_event_%'
  group by yr);

select rc.yr, rc.row_count as raw_row_count, ac.row_count as analytics_row_count
from _raw_count rc
left join _analytics_count ac on rc.yr = ac.yr
order by rc.yr;

drop view if exists _raw_count;
drop view if exists _analytics_count;
