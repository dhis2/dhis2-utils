
--
-- PostgreSQL queries for monitoring performance, slow queries and locks
--

-- Current queries

select pid, datname, usename, query_start, now() - pg_stat_activity.query_start as duration, state, query from pg_catalog.pg_stat_activity where state != 'idle' and query not ilike '%pg_stat_activity%';

-- Count of current queries

select count(*) from pg_catalog.pg_stat_activity where state != 'idle' and query not ilike '%pg_stat_activity%';

-- Queries running for more than 5 minutes

select pid, datname, usename, query_start, now() - pg_stat_activity.query_start as duration, state, query from pg_catalog.pg_stat_activity where (now() - pg_stat_activity.query_start) > interval '5 minutes' and state != 'idle' and query not ilike '%pg_stat_activity%';

-- Count of queries running for more than 5 minutes

select count(*) from pg_catalog.pg_stat_activity where (now() - pg_stat_activity.query_start) > interval '5 minutes' and state != 'idle' and query not ilike '%pg_stat_activity%';

-- Current locks

select pl.locktype, pl.pid, pl.mode, pl.granted, pa.datname, pa.client_addr, pa.query_start, pa.state, pa.query from pg_catalog.pg_locks pl left join pg_stat_activity pa on pl.pid = pa.pid;

-- Count of locks

select count(*) from pg_catalog.pg_locks;

-- Cancel query

select pg_cancel_backend(_pid_);

-- Terminate query

select pg_terminate_backend(_pid_);
