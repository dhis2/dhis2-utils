
--
-- PostgreSQL queries for monitoring performance, slow queries and locks
--

-- Current queries

select pid, datname, usename, query_start, now() - pg_stat_activity.query_start as duration, state, query from pg_catalog.pg_stat_activity;

-- Count of queries

select count(*) from pg_catalog.pg_stat_activity;

-- Queries running for more than 5 minutes

select pid, datname, usename, query_start, now() - pg_stat_activity.query_start as duration, state, query from pg_catalog.pg_stat_activity where (now() - pg_stat_activity.query_start) > interval '5 minutes';

-- Count of queries running for more than 5 minutes

select count(*) from pg_catalog.pg_stat_activity where (now() - pg_stat_activity.query_start) > interval '5 minutes';

-- Current locks

select pl.locktype, pl.pid, pl.mode, pl.granted, pa.datname, pa.client_addr, pa.query_start, pa.state, pa.query from pg_catalog.pg_locks pl left join pg_stat_activity pa on pl.pid = pa.pid;

-- Count of locks

select count(*) from pg_catalog.pg_locks;

--
-- Danger zone
--

-- Cancel query

select pg_cancel_backend(_pid_);

-- Terminate query

select pg_terminate_backend(_pid_);

-- Function for terminating slow queries

drop function if exists terminate_slow_queries;
create function terminate_slow_queries() 
returns integer as $$
declare
	q record;
	c integer := 0;
begin
	for q in select * from pg_catalog.pg_stat_activity where query not like '%pg_catalog%' and query != 'COMMIT' and (now() - pg_stat_activity.query_start) > interval '10 minutes'
	loop
		raise notice 'Terminating PID: %', q.pid;
		perform pg_terminate_backend(q.pid);
		c := c + 1;
	end loop;
	return c;
end;
$$ language plpgsql;

-- Function invocation

select terminate_slow_queries();
