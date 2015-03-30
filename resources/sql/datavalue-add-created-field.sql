-- Update script for datavalue table for addition of the created column
-- If no created column exists in datavalue, the column in created
-- For each row: if created field is null, set value from lastupdated

ALTER TABLE datavalue ADD COLUMN created timestamp without time zone;

UPDATE datavalue 
SET created = lastupdated 
WHERE created IS NULL 
AND lastupdated IS NOT NULL;
