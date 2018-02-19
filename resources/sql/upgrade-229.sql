
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


-- set all tracked entity attributes searchable

update program_attributes set searchable = true;

	
-- migrate userrole.dataSets and userrole.programs to usergroup and apply data sharing
-- after executing below scripts run command "select migrateRoleToUserGroup();" to migrate data. 

CREATE OR REPLACE FUNCTION uid()
RETURNS text AS $$
  SELECT substring('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' 
    FROM (random()*51)::int +1 for 1) || 
    array_to_string(ARRAY(SELECT substring('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' 
       FROM (random()*61)::int + 1 FOR 1) 
   FROM generate_series(1,10)), '') ;
$$ LANGUAGE sql;

create or replace function migrateRoleToUserGroup() returns void as $$
declare role RECORD;
declare curUserGroupId int;
declare roleDataset RECORD;
declare curGroupAccessId int;
declare roleProgram RECORD;
begin
for role in select * from userrole
loop 
	if exists ( select 1 from userroledataset rds where rds.userroleid = role.userroleid )
	then 
		insert into usergroup (usergroupid, name, uid, code, lastupdated, created, userid, publicaccess, lastupdatedby)
		values ( nextval('hibernate_sequence'::regclass), '_DATASET_' || role.name, uid(), null,null,now(), role.userid, 'rw------',null )
		returning usergroup.usergroupid into curUserGroupId;
		for roleDataset in select * from userroledataset
		loop 
			insert into usergroupaccess ( usergroupaccessid, access, usergroupid )
			values ( nextval('hibernate_sequence'::regclass), 'rwrw----', curUserGroupId )
			returning usergroupaccessid into curGroupAccessId;
			insert into datasetusergroupaccesses (datasetid, usergroupaccessid)
			values ( roleDataset.datasetid, curGroupAccessId);
			if not exists ( select 1 from usergroupmembers where usergroupid = curUserGroupId )
			then 
				insert into usergroupmembers ( usergroupid, userid )
				select curUserGroupId, um.userid from userrolemembers um where um.userroleid = role.userroleid;
			end if;
		end loop;
	end if;
	if exists ( select 1 from userroleprogram rds where rds.userroleid = role.userroleid )
	then 
		insert into usergroup (usergroupid, name, uid, code, lastupdated, created, userid, publicaccess, lastupdatedby)
		values ( nextval('hibernate_sequence'::regclass), '_PROGRAM_' || role.name, uid(), null,null,now(), role.userid, 'rw------',null )
		returning usergroup.usergroupid into curUserGroupId;
		for roleProgram in select * from userroleprogram
		loop 
			insert into usergroupaccess ( usergroupaccessid, access, usergroupid )
			values ( nextval('hibernate_sequence'::regclass), 'rwrw----', curUserGroupId )
			returning usergroupaccessid into curGroupAccessId;
			insert into programusergroupaccesses (programid, usergroupaccessid)
			values ( roleProgram.programid, curGroupAccessId);
			if not exists ( select 1 from usergroupmembers where usergroupid = curUserGroupId )
			then 
				insert into usergroupmembers ( usergroupid, userid )
				select curUserGroupId, um.userid from userrolemembers um where um.userroleid = role.userroleid;
			end if;
		end loop;
	end if;
end loop;
end;
$$ language plpgsql;

--- rollback scripts for migrate data sharing 

-- delete from datasetusergroupaccesses where usergroupaccessid in ( select usergroupaccessid from usergroupaccess uga inner join usergroup ug on uga.usergroupid = ug.usergroupid and ug.name like '_DATASET_%');
-- delete from programusergroupaccesses where usergroupaccessid in ( select usergroupaccessid from usergroupaccess uga inner join usergroup ug on uga.usergroupid = ug.usergroupid and ug.name like '_PROGRAM_%');
-- delete from usergroupaccess where usergroupid in ( select usergroupid from usergroup where name  like '_DATASET_%' or name like '_PROGRAM_%');
-- delete from usergroupmembers where usergroupid in ( select usergroupid from usergroup where name  like '_DATASET_%' or name like '_PROGRAM_%' );
-- delete from usergroup where name  like '_DATASET_%' or name like '_PROGRAM_%';