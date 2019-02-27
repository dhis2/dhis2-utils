
-- List all integer primary keys in the database

select tc.table_schema, tc.table_name, kc.column_name, cl.udt_name, 'select ' || kc.column_name || ' as id from ' || tc.table_name || ' union all ' as script
from  
    information_schema.table_constraints tc
    inner join information_schema.key_column_usage kc on (kc.table_name = tc.table_name and kc.table_schema = tc.table_schema and kc.constraint_name = tc.constraint_name)
    inner join information_schema.columns cl on (cl.table_name = kc.table_name and cl.table_schema = kc.table_schema and cl.column_name = kc.column_name)
where 
    tc.constraint_type = 'PRIMARY KEY' 
    and kc.column_name != 'sort_order'
    and cl.udt_name = 'int4'
order by 1, 2, 3;

