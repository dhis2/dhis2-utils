
-- PostgreSQL sorting performs very badly on Lao character based strings 
-- using the default collation. This script will set the Lao collation which
-- improves sort performance.

alter table reporttable alter column name set data type varchar(230) collate "lo-x-icu";
reindex table reporttable;

alter table chart alter column name set data type varchar(230) collate "lo-x-icu";
reindex table chart;

alter table map alter column name set data type varchar(230) collate "lo-x-icu";
reindex table map;

alter table organisationunit alter column name set data type varchar(230) collate "lo-x-icu";
alter table organisationunit alter column shortname set data type varchar(50) collate "lo-x-icu";
reindex table organisationunit;

alter table dataelement alter column name set data type varchar(230) collate "lo-x-icu";
alter table dataelement alter column shortname set data type varchar(50) collate "lo-x-icu";
reindex table dataelement;

alter table dataelementcategoryoption alter column name set data type varchar(230) collate "lo-x-icu";
alter table dataelementcategoryoption alter column shortname set data type varchar(50) collate "lo-x-icu";
reindex table dataelementcategoryoption;
