
--
-- PostgreSQL queries for monitoring performance, slow queries and locks.
--
-- Enable sloq query logging in postgresql.conf:
--
-- log_statement = none
-- log_min_duration_statement = 200
--

-- Current queries

select pid, datname, usename, query_start, now() - pg_stat_activity.query_start as duration, state, query 
from pg_catalog.pg_stat_activity 
where state != 'idle' 
and query not ilike '%pg_stat_activity%';

-- Count of current queries

select count(*) 
from pg_catalog.pg_stat_activity 
where state != 'idle' 
and query not ilike '%pg_stat_activity%';

-- Last queries

select pid, datname, usename, query_start, now() - pg_stat_activity.query_start as duration, state, query 
from pg_catalog.pg_stat_activity 
where query not ilike '%pg_stat_activity%';

-- Count of last queries

select count(*) 
from pg_catalog.pg_stat_activity 
where query not ilike '%pg_stat_activity%';

-- Queries running for more than 1 minute

select pid, datname, usename, query_start, now() - pg_stat_activity.query_start as duration, state, query 
from pg_catalog.pg_stat_activity 
where (now() - pg_stat_activity.query_start) > interval '5 minutes' 
and state != 'idle' 
and query not ilike '%pg_stat_activity%';

-- Count of queries running for more than 1 minutes

select count(*) 
from pg_catalog.pg_stat_activity 
where (now() - pg_stat_activity.query_start) > interval '1 minutes' 
and state != 'idle' 
and query not ilike '%pg_stat_activity%';

-- Current locks

select pl.pid, pl.locktype, pl.mode, pl.granted, pa.datname, pa.client_addr, pa.query_start, pa.state, pa.query 
from pg_catalog.pg_locks pl 
left join pg_stat_activity pa on pl.pid = pa.pid;

-- Count of locks

select count(*) 
from pg_catalog.pg_locks;

-- Locks older than 10 minutes

select pl.pid, pl.locktype, pl.mode, pl.granted, pa.datname, pa.client_addr, pa.query_start, pa.state, pa.query
from pg_catalog.pg_locks pl
inner join pg_stat_activity pa on pl.pid = pa.pid
where (now() - pa.query_start) > interval '10 minutes';

-- Count of connections

select sum(numbackends) 
from pg_stat_database;

-- Cancel query

select pg_cancel_backend(_pid_);

-- Terminate query

select pg_terminate_backend(_pid_);

-- Blocked and blocking activity

select blocked_locks.pid as blocked_pid, blocked_activity.usename as blocked_user, blocking_locks.pid as blocking_pid, blocking_activity.usename as blocking_user, blocked_activity.query as blocked_statement, blocking_activity.query as current_statement_in_blocking_process
from pg_catalog.pg_locks blocked_locks
    join pg_catalog.pg_stat_activity blocked_activity on blocked_activity.pid = blocked_locks.pid
    join pg_catalog.pg_locks blocking_locks on blocking_locks.locktype = blocked_locks.locktype
        and blocking_locks.database is not distinct from blocked_locks.database
        and blocking_locks.relation is not distinct from blocked_locks.relation
        and blocking_locks.page is not distinct from blocked_locks.page
        and blocking_locks.tuple is not distinct from blocked_locks.tuple
        and blocking_locks.virtualxid is not distinct from blocked_locks.virtualxid
        and blocking_locks.transactionid is not distinct from blocked_locks.transactionid
        and blocking_locks.classid is not distinct from blocked_locks.classid
        and blocking_locks.objid is not distinct from blocked_locks.objid
        and blocking_locks.objsubid is not distinct from blocked_locks.objsubid
        and blocking_locks.pid != blocked_locks.pid
    join pg_catalog.pg_stat_activity blocking_activity on blocking_activity.pid = blocking_locks.pid
where not blocked_locks.granted;

-- Show performance related settings

show max_connections; show shared_buffers; show work_mem; show maintenance_work_mem; show effective_cache_size; show checkpoint_completion_target; show synchronous_commit; show wal_writer_delay;

-- Enable and disable logging

alter system set log_statement = 'all';
select pg_reload_conf();
show log_statement;

alter system set log_statement = 'none';
select pg_reload_conf();
show log_statement;

