-- Add deleted column to datavalue table

alter table datavalue add column deleted boolean;
update datavalue set deleted = false where deleted is null;
alter table datavalue alter column deleted set not null;
create index in_datavalue_deleted on datavalue(deleted);

