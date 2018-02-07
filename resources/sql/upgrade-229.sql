
-- 2.29 upgrade script

-- rename tables and columns from "tracked entity" to "tracked entity type"

alter table trackedentity rename to trackedentitytype;
alter table trackedentitytype rename trackedentityid to trackedentitytypeid;

alter table program rename trackedentityid to trackedentitytypeid;
alter table program rename constraint fk_program_trackedentityid to fk_program_trackedentitytypeid;

alter table trackedentityinstance rename trackedentityid to trackedentitytypeid;
alter table trackedentityinstance rename constraint fk_trackedentityinstance_trackedentityid to fk_trackedentityinstance_trackedentitytypeid;

alter table attribute rename trackedentityattribute to trackedentitytypeattribute;

alter table trackedentityattributevalues rename to trackedentitytypeattributevalues;
alter table trackedentitytypeattributevalues rename trackedentityid to trackedentitytypeid;

alter table trackedentitytranslations rename trackedentityid to trackedentitytypeid;            
alter table trackedentitytranslations rename constraint fk_objecttranslation_trackedentityid to fk_objecttranslation_trackedentitytypeid;

-- grant data read sharing to users for objects which have metadata read sharing 

update program set publicaccess = 'rwr-----' where publicaccess = 'rw------';
update program set publicaccess = 'r-r-----' where publicaccess = 'r-------';
update programstage set publicaccess = 'rwr-----' where publicaccess = 'rw------';
update programstage set publicaccess = 'r-r-----' where publicaccess = 'r-------';
update dataset set publicaccess = 'rwr-----' where publicaccess = 'rw------';
update dataset set publicaccess = 'r-r-----' where publicaccess = 'r-------';
update dataelementcategoryoption set publicaccess = 'rwr-----' where publicaccess = 'rw------';
update dataelementcategoryoption set publicaccess = 'r-r-----' where publicaccess = 'r-------';

update usergroupaccess set access = 'rwr-----' where access = 'rw------' and usergroupaccessid in (
  select usergroupaccessid from programusergroupaccesses
  union all select usergroupaccessid from programstageuseraccesses
  union all select usergroupaccessid from datasetuseraccesses
  union all select usergroupaccessid from dataelementcategoryoption);

update usergroupaccess set access = 'r-r-----' where access = 'r-------' and usergroupaccessid in (
  select usergroupaccessid from programusergroupaccesses
  union all select usergroupaccessid from programstageuseraccesses
  union all select usergroupaccessid from datasetuseraccesses
  union all select usergroupaccessid from dataelementcategoryoption);
