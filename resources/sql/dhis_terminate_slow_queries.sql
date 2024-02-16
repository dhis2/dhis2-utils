
-- Function for terminating slow queries generated by DHIS 2

-- Excludes queries from psql, pg_dump (backup), PostgreSQL maintenance and DHIS 2 analytics table generation

-- Adjust username filter as necessary, set to 'dhis' by default. For regular use, use `dhis_cancel_show_queries()` instead.

-- To invoke run $ select dhis_terminate_slow_queries();

-- Create view

create or replace view dhis_slow_queries as 
select * from pg_catalog.pg_stat_activity 
where usename = 'dhis' 
and application_name not in ('psql', 'pg_dump') 
and query ilike 'select%' 
and query !~* ('pg_catalog|information_schema|pg_temp|pg_toast');

-- Create function

create or replace function dhis_terminate_slow_queries()
returns integer as $$
declare
    q record;
    c integer := 0;
begin
    for q in select * from dhis_slow_queries
    loop
        raise notice 'Terminating query with PID: %', q.pid;
        perform pg_terminate_backend(q.pid);
        c := c + 1;
    end loop;
    return c;
end;
$$ language plpgsql;
