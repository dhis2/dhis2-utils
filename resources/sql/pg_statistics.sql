--
-- Statistics queries for PostgreSQL
--

-- SIZE

-- Size of database

select pg_size_pretty(pg_database_size('dhis2'));

-- Size of largest tables

select tb.table_schema as table_schema, tb.table_name, pg_size_pretty(pg_relation_size(quote_ident(tb.table_name))) as table_size
from information_schema.tables tb
where tb.table_schema = 'public'
order by pg_relation_size(quote_ident(tb.table_name)) desc
limit 500;

-- Size of temp files being created since database was created

select datname, temp_files, temp_bytes as temp_files_size_bytes, pg_size_pretty(temp_bytes) as temp_files_size_pretty
from pg_stat_database db
where datname = 'dhis2';

-- COUNT

-- Approximate count of largest tables

select c.relname as table_name, s.nspname as table_schema, c.reltuples::bigint as approximate_row_count
from pg_catalog.pg_class c
inner join pg_catalog.pg_namespace s on c.relnamespace = s.oid
inner join information_schema.tables t on c.relname = t.table_name and s.nspname = t.table_schema 
where t.table_type = 'BASE TABLE'
and c.relname !~ '^_?pg_.*$'
order by approximate_row_count desc
limit 200;

-- Approximate count of rows in datavalue table

select reltuples::bigint as approximate_row_count 
from pg_class 
where relname = 'datavalue';

-- Count of data values by year

select extract(year from pe.startdate)::integer as yr, count(*) as row_count
from datavalue dv
inner join period pe on dv.periodid = pe.periodid
group by yr
order by yr;

-- Count of events by program

select p.uid, p.shortname, (
  select count(*)
  from programstageinstance psi
  inner join programinstance pi on psi.programinstanceid = pi.programinstanceid
  where pi.programid = p.programid) as event_count
from program p
order by event_count desc;

-- Approximate count of rows in tracker data tables

select relname, reltuples::bigint as approximate_row_count 
from pg_class 
where relname in ('trackedentityinstance', 'trackedentityattributevalue', 'programinstance', 'programstageinstance');

-- Approximate count of rows for large tables

select relname as table_name, reltuples::bigint as approximate_row_count 
from pg_class 
where relname in ('completedatasetregistration', 'dataset', 'datavalue', 'datavalueaudit', 'program', 'programinstance', 
  'programstageinstance', 'trackedentityinstance', 'trackedentityattributevalue', 'trackedentitydatavalueaudit');

-- Approximate count of rows for all relations by schema

select ns.nspname as schema_name, rl.relname as table_name, rl.oid as object_id, rl.reltuples::bigint as approximate_row_count 
from pg_catalog.pg_class rl
inner join pg_catalog.pg_namespace ns on rl.relnamespace = ns.oid
where ns.nspname not in ('information_schema', 'pg_catalog', 'pg_toast')
order by schema_name, table_name;

-- Approximate count of rows in analytics tables

select relname as table_name, reltuples::bigint as approximate_row_count
from pg_class
where relname like 'analytics%'
order by approximate_row_count desc;

-- Count of indexes and columns and completion by analytics table

with table_data as (
  select t.table_schema, t.table_name, (
    select count(i.indexname)
    from pg_catalog.pg_indexes i
    where i.schemaname = t.table_schema
    and i.tablename = t.table_name) as index_count, (
    select count(c.column_name)
    from information_schema.columns c
    where c.table_schema = t.table_schema
    and c.table_name = t.table_name) as column_count
  from information_schema.tables t)
select table_schema, table_name, index_count, column_count, 
  round((index_count::numeric / column_count::numeric * 100), 2) as percentage_completed
from table_data t
where t.table_schema = 'public'
and t.table_name like 'analytics%'
order by t.table_schema, t.table_name;

-- Count of scans for indexes

select
  relname as table_name,
  indexrelname as index_name,
  idx_scan as number_of_scans,
  idx_tup_read as tuples_read,
  idx_tup_fetch as tuples_fetched
from
  pg_stat_user_indexes
inner join
  pg_indexes on pg_stat_user_indexes.indexrelname = pg_indexes.indexname
order by
  idx_scan desc;

-- Time of last vacuum and analyze by table

select relname as table_name, n_dead_tup as dead_tuples, 
  last_vacuum, last_autovacuum, last_analyze, last_autoanalyze
from pg_stat_user_tables
where relname = 'datavalue';

-- Time of last vacuum and analyze for largest tables

select
  s.nspname as table_schema,
  c.relname as table_name,
  c.reltuples::bigint as approximate_row_count,
  u.n_dead_tup as dead_tuples,
  u.last_vacuum::timestamp(0) as last_vacuum,
  u.last_autovacuum::timestamp(0) as last_auto_vacuum,
  u.last_analyze::timestamp(0) as last_analyze,
  u.last_autoanalyze::timestamp(0) as last_auto_analyze
from pg_catalog.pg_class c
inner join pg_catalog.pg_namespace s on c.relnamespace = s.oid
inner join information_schema.tables t on c.relname = t.table_name and s.nspname = t.table_schema
inner join pg_stat_user_tables u on c.relname = u.relname and s.nspname = u.schemaname
where t.table_type = 'BASE TABLE'
and c.relname !~ '^_?pg_.*$'
order by approximate_row_count desc
limit 200;
