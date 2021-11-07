
-- SIZE

-- Get size of database

select pg_size_pretty(pg_database_size('dhis2'));

-- Get size of largest tables

select tb.table_schema as table_schema, tb.table_name, pg_size_pretty(pg_relation_size(quote_ident(tb.table_name))) as table_size
from information_schema.tables tb
where tb.table_schema = 'public'
order by pg_relation_size(quote_ident(tb.table_name)) desc
limit 100;

-- Get size of temp files being created since database was created

select datname, temp_files, temp_bytes as temp_files_size_bytes, pg_size_pretty(temp_bytes) as temp_files_size_pretty
from pg_stat_database db
where datname = 'dhis2';

-- Approximate count of rows in datavalue table

select reltuples::bigint as approximate_row_count 
from pg_class 
where relname = 'datavalue';

-- Approximate count of rows in tracker data tables

select relname, reltuples::bigint as approximate_row_count 
from pg_class 
where relname in ('trackedentityinstance', 'trackedentityattributevalue', 'programinstance', 'programstageinstance')
order by relname;

-- ANALYTICS

-- Approximate count of rows in analytics tables

select relname as table_name, reltuples::bigint as approximate_row_count
from pg_class
where relname like 'analytics_%'
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
