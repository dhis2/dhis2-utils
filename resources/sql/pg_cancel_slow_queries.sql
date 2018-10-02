
-- Function for cancelling slow queries

-- To invoke run $ select dhis_cancel_slow_queries();

drop function if exists dhis_cancel_slow_queries;

create function dhis_cancel_slow_queries()
returns integer as $$
declare
	q record;
	c integer := 0;
begin
	for q in select * from pg_catalog.pg_stat_activity where (now() - pg_stat_activity.query_start) > interval '15 minutes' and state != 'idle' and query not ilike '%pg_stat_activity%';
	loop
		raise notice 'Terminating PID: %', q.pid;
		perform pg_cancel_backend(q.pid);
		c := c + 1;
	end loop;
	return c;
end;
$$ language plpgsql;
