
--- migrate userrole.dataSets and userrole.programs to usergroup



CREATE OR REPLACE FUNCTION uid()
RETURNS text AS $$
  SELECT substring('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' 
    FROM (random()*51)::int +1 for 1) || 
    array_to_string(ARRAY(SELECT substring('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' 
       FROM (random()*61)::int + 1 FOR 1) 
   FROM generate_series(1,10)), '') ;
$$ LANGUAGE sql;

create or replace function migrateRoleToUG() returns void as $$
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
