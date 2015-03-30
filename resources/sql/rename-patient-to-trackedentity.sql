
-- tabular report

DROP TABLE patientaggregatereport_dimension;
DROP TABLE patientaggregatereport_filters;
DROP TABLE patientaggregatereportmembers;
DROP TABLE patientaggregatereportusergroupaccesses;
DROP TABLE patientaggregatereport;

ALTER TABLE programstage_dataelements DROP COLUMN patienttabularreportid;
DROP TABLE dashboarditem_patienttabularreports;
DROP TABLE patienttabularreport_dimensions;
DROP TABLE patienttabularreport_filters;
DROP TABLE patienttabularreportmembers;
DROP TABLE patienttabularreportusergroupaccesses;
DROP TABLE patienttabularreport;

-- attribute option

ALTER TABLE patientattributevalue DROP COLUMN patientattributeoptionid;

-- patient

alter table patient rename to trackedentityinstance;
ALTER TABLE trackedentityinstance RENAME COLUMN patientid TO trackedentityinstanceid;
ALTER TABLE trackedentityinstance RENAME CONSTRAINT patient_pkey TO trackedentityinstance_pkey;
ALTER TABLE trackedentityinstance RENAME CONSTRAINT fk_patient_organisationunitid TO fk_trackedentityinstance_organisationunitid;
ALTER TABLE trackedentityinstance RENAME CONSTRAINT fk_user_patientid TO fk_user_trackedentityinstance;

-- attribute

alter table patientattribute rename to trackedentityattribute;
ALTER TABLE trackedentityattribute RENAME COLUMN patientattributeid TO trackedentityattributeid;
ALTER TABLE trackedentityattribute RENAME COLUMN patientattributegroupid TO trackedentityattributegroupid;
ALTER TABLE trackedentityattribute RENAME CONSTRAINT patientattribute_pkey TO trackedentityattribute_pkey;
ALTER TABLE trackedentityattribute RENAME CONSTRAINT patientattribute_code_key TO trackedentityattribute_code_key;
ALTER TABLE trackedentityattribute RENAME CONSTRAINT patientattribute_name_key TO trackedentityattribute_name_key;

-- atttribute group

alter table patientattributegroup rename to trackedentityattributegroup;
ALTER TABLE trackedentityattributegroup RENAME COLUMN patientattributegroupid TO trackedentityattributegroupid;
ALTER TABLE trackedentityattributegroup RENAME CONSTRAINT patientattributegroup_pkey TO trackedentityattributegroup_pkey;
ALTER TABLE trackedentityattributegroup RENAME CONSTRAINT patientattributegroup_code_key TO trackedentityattributegroup_code_key;
ALTER TABLE trackedentityattributegroup RENAME CONSTRAINT patientattributegroup_name_key TO trackedentityattributegroup_name_key;

-- audit

alter table patientaudit rename to trackedentityaudit;
ALTER TABLE trackedentityaudit RENAME COLUMN patientid TO trackedentityinstanceid;
ALTER TABLE trackedentityaudit RENAME COLUMN patientauditid TO trackedentityauditid;
ALTER TABLE trackedentityaudit RENAME CONSTRAINT patientaudit_pkey TO trackedentityaudit_pkey;
ALTER TABLE trackedentityaudit RENAME CONSTRAINT fk_patientauditid_patientid TO fk_trackedentityauditid_trackedentityinstanceid;

-- form

alter table patientregistrationform rename to trackedentityform;
ALTER TABLE trackedentityform RENAME COLUMN patientregistrationformid TO trackedentityformid;
ALTER TABLE trackedentityform RENAME CONSTRAINT patientregistrationform_pkey TO trackedentityform_pkey;
ALTER TABLE trackedentityform RENAME CONSTRAINT fk_patientregistrationform_programid TO fk_trackedentityform_programid;
ALTER TABLE trackedentityform RENAME CONSTRAINT fk_patientregistrationform_dataentryformid TO fk_trackedentityform_dataentryformid;

DROP TABLE patientregistrationform_attributes;
DROP TABLE patientregistrationform_fixedattributes;
DROP TABLE patientregistrationform_identifiertypes;
DROP TABLE patientregistrationform_attributes;

-- reminder

alter table patientreminder rename to trackedentityinstancereminder;
ALTER TABLE trackedentityinstancereminder RENAME COLUMN patientreminderid TO trackedentityinstancereminderid;
ALTER TABLE trackedentityinstancereminder RENAME CONSTRAINT patientreminder_pkey TO trackedentityinstancereminder_pkey;
ALTER TABLE trackedentityinstancereminder RENAME CONSTRAINT fk_patientreminder_usergroup TO fk_trackedentityinstancereminder_programid;

-- attribute value

alter table patientattributevalue rename to trackedentityattributevalue;
ALTER TABLE trackedentityattributevalue RENAME COLUMN patientid TO trackedentityinstanceid;
ALTER TABLE trackedentityattributevalue RENAME COLUMN patientattributeid TO trackedentityattributeid;
ALTER TABLE trackedentityattributevalue RENAME CONSTRAINT patientattributevalue_pkey TO trackedentityattributevalue_pkey;
ALTER TABLE trackedentityattributevalue RENAME CONSTRAINT fk_patientattributevalue_patientattributeid TO fk_attributevalue_attributeid;
ALTER TABLE trackedentityattributevalue RENAME CONSTRAINT fk_patientattributevalue_patientid TO fk_attributevalue_trackedentityinstanceid;

-- comment

alter table patientcomment rename to trackedentitycomment;
ALTER TABLE trackedentitycomment RENAME COLUMN patientcommentid TO trackedentitycommentid;
ALTER TABLE trackedentitycomment RENAME CONSTRAINT patientcomment_pkey TO trackedentitycomment_pkey;

-- data value

alter table patientdatavalue rename to trackedentitydatavalue;
ALTER TABLE trackedentitydatavalue RENAME CONSTRAINT patientdatavalue_pkey TO trackedentitydatavalue_pkey;
ALTER TABLE trackedentitydatavalue RENAME CONSTRAINT fk_patientdatavalue_dataelementid TO fk_entityinstancedatavalue_dataelementid;
ALTER TABLE trackedentitydatavalue RENAME CONSTRAINT fk_patientdatavalue_programstageinstanceid TO fk_entityinstancedatavalue_programstageinstanceid;

-- relationship

ALTER TABLE relationship RENAME COLUMN patientaid TO trackedentityinstanceaid;
ALTER TABLE relationship RENAME COLUMN patientbid TO trackedentityinstancebid;
ALTER TABLE relationship RENAME CONSTRAINT fk_relationship_patientida TO fk_relationship_trackedentityinstanceida;
ALTER TABLE relationship RENAME CONSTRAINT fk_relationship_patientidb TO fk_relationship_trackedentityinstanceidb;

-- mobile setting

ALTER TABLE patientmobilesetting rename to trackedentitymobilesetting;
ALTER TABLE trackedentitymobilesetting RENAME COLUMN patientmobilesettingid TO trackedentitymobilesettingid;
ALTER TABLE trackedentitymobilesetting RENAME CONSTRAINT patientmobilesetting_pkey TO trackedentitymobilesetting_pkey;

-- program attributes (should fail if not run on 2.14)

ALTER TABLE program_attributes RENAME COLUMN programattributeid TO programtrackedentityattributeid;
ALTER TABLE program_attributes RENAME COLUMN attributeid TO trackedentityattributeid; 

-- program instance

ALTER TABLE programinstance RENAME COLUMN patientcommentid TO trackedentitycommentid;
ALTER TABLE programinstance RENAME COLUMN patientid TO trackedentityinstanceid;

-- program stage instance

ALTER TABLE programstageinstance RENAME COLUMN patientcommentid TO trackedentitycommentid;
ALTER TABLE trackedentityattribute RENAME COLUMN patientmobilesettingid TO trackedentitymobilesettingid;
ALTER TABLE trackedentityattribute RENAME COLUMN sort_order_patientattributename TO sort_order_trackedentityattributename;

-- mobile setting

DROP TABLE patientmobilesetting;

-- tables to migrate before dropping

-- DROP TABLE program_patientidentifiertypes;
-- DROP TABLE patientidentifiertype;
-- DROP TABLE patientidentifier;
-- DROP TABLE patientattributeoption;

