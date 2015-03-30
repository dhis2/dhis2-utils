-- Removes tables from India modules from database, handy if WAR is accidentally deployed on database

﻿drop table config_in cascade;
drop table detarget cascade;
drop table detargetdatavalue cascade;
drop table detargetmember cascade;
drop table detargetsource cascade;
drop table linelist_de_map cascade;
drop table linelistelement cascade;
drop table linelistelementoptions cascade;
drop table linelistgroup cascade;
drop table linelistgroupelements cascade;
drop table linelistlockedperiods cascade;
drop table linelistoption cascade;
drop table linelistsource cascade;
drop table linelistvalidationrule cascade;
drop table llaggregation cascade;
drop table lldataelementmapping cascade;
drop table lldatavalue cascade;
drop table reportin cascade;
drop table reportsource cascade;
drop table survey cascade;
drop table surveydatavalue cascade;
drop table surveymembers cascade;
drop table surveysource cascade;
drop table targetmapping cascade;
