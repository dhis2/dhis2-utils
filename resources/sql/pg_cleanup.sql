
-- Utility queries for assistance in cleaning up and removing metadata and data

-- Get foreign keys referring to a specific table

select conrelid::regclass AS foreign_table,
  conname AS constraint_name,
  a.attname AS foreign_column,
  confrelid::regclass AS referenced_table,
  af.attname AS referenced_column,
  pg_get_constraintdef(c.oid) AS constraint_definition
from pg_constraint c
  inner join pg_attribute a ON a.attnum = ANY(c.conkey) AND a.attrelid = c.conrelid
  inner join pg_attribute af ON af.attnum = ANY(c.confkey) AND af.attrelid = c.confrelid
where confrelid = 'organisationunit'::regclass
  and c.contype = 'f';

