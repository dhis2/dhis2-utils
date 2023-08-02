
-- SIZE

-- Size of database

select pg_size_pretty(pg_database_size('dhis2'));

-- Size of largest tables

select tb.table_schema as table_schema, tb.table_name, pg_size_pretty(pg_relation_size(quote_ident(tb.table_name))) as table_size
from information_schema.tables tb
where tb.table_schema = 'public'
order by table_size desc
limit 500;

-- Size of temp files being created since database was created

select datname, temp_files, temp_bytes as temp_files_size_bytes, pg_size_pretty(temp_bytes) as temp_files_size_pretty
from pg_stat_database db
where datname = 'dhis2';

-- Approximate count of largest tables


select c.relname as table_name, s.nspname as table_schema, c.reltuples::bigint as approximate_row_count
from pg_catalog.pg_class c
inner join pg_catalog.pg_namespace s on c.relnamespace=s.oid
inner join information_schema.tables t on c.relname = t.table_name and s.nspname = t.table_schema 
where t.table_type = 'BASE TABLE'
and c.relname !~ '^_?pg_.*$'
order by approximate_row_count desc
limit 200;

-- Approximate count of rows in datavalue table

select reltuples::bigint as approximate_row_count 
from pg_class 
where relname = 'datavalue';

-- Approximate count of rows in tracker data tables

select relname, reltuples::bigint as approximate_row_count 
from pg_class 
where relname in ('trackedentityinstance', 'trackedentityattributevalue', 'programinstance', 'programstageinstance');

-- Approximate count of rows for large tables

select relname as table_name, reltuples::bigint as approximate_row_count 
from pg_class 
where relname in ('completedatasetregistration', 'dataset', 'datavalue', 'datavalueaudit',
  'program', 'programinstance', 'programstageinstance'
	'trackedentityinstance', 'trackedentityattributevalue', 'trackedentitydatavalueaudit');

-- Approximate count of rows for all relations by schema

select ns.nspname as schema_name, rl.relname as table_name, rl.oid as object_id, rl.reltuples::bigint as approximate_row_count 
from pg_catalog.pg_class rl
inner join pg_catalog.pg_namespace ns on rl.relnamespace = ns.oid
where ns.nspname not in ('information_schema', 'pg_catalog', 'pg_toast')
order by schema_name, table_name;

-- ANALYTICS

-- Approximate count of rows in analytics tables

select relname as table_name, reltuples::bigint as approximate_row_count
from pg_class
where relname like 'analytics_%'
order by approximate_row_count desc;
