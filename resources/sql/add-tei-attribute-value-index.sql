
-- Add btree index on table trackedentityattributevalue
-- Ensure there are no rows where the 'value' column is longer than 1200 chars

-- List all values that exceeds 1200 characters
SELECT value FROM trackedentityattributevalue WHERE length(value) > 1200;

-- Delete all values that exceeds 1200 characters (be careful)
DELETE FROM trackedentityattributevalue WHERE length(value) > 1200;

-- Change the data type (done by DHIS2 during upgrade)
ALTER TABLE trackedentityattributevalue 
ALTER COLUMN value SET DATA TYPE VARCHAR(1200);

-- Adding the btree index (Done by DHIS2 during upgrade)
CREATE INDEX in_trackedentity_attribute_value 
ON trackedentityattributevalue USING btree (trackedentityattributeid, LOWER(value));
