
-- Upgrade program data entry form foreign keys

ALTER TABLE programstage DROP CONSTRAINT fk_programstage_dataentryform;
ALTER TABLE programstage ADD CONSTRAINT fk_programstage_dataentryform FOREIGN KEY (dataentryform) REFERENCES dataentryform (dataentryformid) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION;

ALTER TABLE trackedentityform DROP CONSTRAINT fk_trackedentityform_dataentryformid;
ALTER TABLE trackedentityform ADD CONSTRAINT fk_trackedentityform_dataentryformid FOREIGN KEY (dataentryform) REFERENCES dataentryform (dataentryformid) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION;
