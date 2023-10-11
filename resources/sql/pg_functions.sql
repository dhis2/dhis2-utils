--
-- Utility functions for PostgreSQL
--

-- Get approximate row count of table in a performant way
--
-- Usage: select approx_count('table_name')

create or replace function approx_count(table_name text)
returns bigint as
$$
declare
  row_count_estimate bigint;
begin
  select reltuples into row_count_estimate
  from pg_class 
  where relname = table_name;
  
  return row_count_estimate;
end;
$$
language plpgsql;
