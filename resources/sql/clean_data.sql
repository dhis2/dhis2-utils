
-- Script which removes all data related tables,
-- which includes data value, tracked entity instance and program stage instance related tables

-- Create function

drop function if exists delete_rows_from_tables;

create or replace function delete_rows_from_tables(tables_to_delete text[])
returns void as
$$
declare
  table_name text;
begin
  foreach table_name in array tables_to_delete
  loop
    execute 'delete from "' || table_name || '"';
  end loop;
end;
$$
language plpgsql;

-- Remove data

select delete_rows_from_tables(array[
'datavalue',
'programownershiphistory',
'trackedentitydatavalueaudit',
'trackedentityattributevalueaudit',
'trackedentityinstanceaudit',
'programstageinstance_messageconversation',
'programstageinstancecomments',
'programinstancecomments',
'programstageinstance',
'trackedentityattributevalue',
'trackedentityprogramowner',
'trackedentityinstance'
]);

-- Delete programinstance rows except default
