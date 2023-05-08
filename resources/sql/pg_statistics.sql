
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

select t.relname, s.nspname, t.reltuples::bigint as approximate_row_count
from pg_catalog.pg_class t
inner join pg_catalog.pg_namespace s on t.relnamespace=s.oid
where relname !~ '^_?pg_.*$'
order by approximate_row_count desc
limit 500;

-- Approximate count of rows in datavalue table

select reltuples::bigint as approximate_row_count 
from pg_class 
where relname = 'datavalue';

-- Approximate count of rows in tracker data tables

select relname, reltuples::bigint as approximate_row_count 
from pg_class 
where relname in ('trackedentityinstance', 'trackedentityattributevalue', 'programinstance', 'programstageinstance')
order by relname;

-- Approximate count of rows for all relations by schema

select ns.nspname as schema_name, rl.relname as table_name, rl.oid as object_id, reltuples::bigint as approximate_row_count 
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
