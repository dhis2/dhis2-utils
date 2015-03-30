
-- Execute: mysql db_name -u user -p < mysql-dhis-upgrade-2.3.sql -f

ALTER TABLE categories_categoryoptions ENGINE = innodb;
ALTER TABLE categorycombo ENGINE = innodb;
ALTER TABLE categorycombos_categories ENGINE = innodb;
ALTER TABLE categorycombos_optioncombos ENGINE = innodb;
ALTER TABLE categoryoptioncombo ENGINE = innodb;
ALTER TABLE categoryoptioncombos_categoryoptions ENGINE = innodb;
ALTER TABLE dataelement ENGINE = innodb;
ALTER TABLE dataelementcategory ENGINE = innodb;
ALTER TABLE dataelementcategoryoption ENGINE = innodb;
ALTER TABLE dataentryform ENGINE = innodb;
ALTER TABLE patientattribute ENGINE = innodb;
ALTER TABLE patientattributegroup ENGINE = innodb;
ALTER TABLE patientattributeoption ENGINE = innodb;
ALTER TABLE program ENGINE = innodb;
ALTER TABLE programstage ENGINE = innodb;
ALTER TABLE programstage_dataelements ENGINE = innodb;
ALTER TABLE userroleauthorities ENGINE = innodb;
ALTER TABLE userroledataset ENGINE = innodb;

-- aggregateddatasetcompleteness table --
ALTER TABLE aggregateddatasetcompleteness DROP COLUMN reporttableid;
ALTER TABLE aggregateddatasetcompleteness MODIFY datasetid INT(11) DEFAULT  NULL;
ALTER TABLE aggregateddatasetcompleteness MODIFY periodid INT(11) DEFAULT NULL;
ALTER TABLE aggregateddatasetcompleteness MODIFY periodname VARCHAR(30) DEFAULT NULL;
ALTER TABLE aggregateddatasetcompleteness MODIFY organisationunitid INT(11) DEFAULT NULL;
ALTER TABLE aggregateddatasetcompleteness DROP INDEX aggregateddatasetcompleteness_index;
ALTER TABLE aggregateddatasetcompleteness DROP PRIMARY KEY;

-- aggregateddatavalue table --
ALTER TABLE aggregateddatavalue MODIFY dataelementid INT(11) DEFAULT  NULL;
ALTER TABLE aggregateddatavalue MODIFY categoryoptioncomboid INT(11) DEFAULT NULL;
ALTER TABLE aggregateddatavalue MODIFY periodid VARCHAR(30) DEFAULT NULL;
ALTER TABLE aggregateddatavalue MODIFY organisationunitid INT(11) DEFAULT NULL;
ALTER TABLE aggregateddatavalue ADD COLUMN modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
ALTER TABLE aggregateddatavalue DROP PRIMARY KEY;
	
-- aggregatedindicatorvalue table --
ALTER TABLE aggregatedindicatorvalue MODIFY indicatorid INT(11) DEFAULT  NULL;
ALTER TABLE aggregatedindicatorvalue MODIFY periodid VARCHAR(30) DEFAULT NULL;
ALTER TABLE aggregatedindicatorvalue MODIFY organisationunitid INT(11) DEFAULT NULL;
ALTER TABLE aggregatedindicatorvalue ADD COLUMN modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;
ALTER TABLE aggregatedindicatorvalue DROP PRIMARY KEY;

-- categories_categoryoptions table --
ALTER TABLE categories_categoryoptions DROP INDEX FKF453B3BDD24076B3;
ALTER TABLE categories_categoryoptions ADD CONSTRAINT fk_category_categoryoptionid FOREIGN KEY (categoryoptionid)
    REFERENCES dataelementcategoryoption(categoryoptionid) ON DELETE RESTRICT ON UPDATE RESTRICT;

-- categorycombos_categories table --
ALTER TABLE categorycombos_categories DROP INDEX FK731150B827F29FF;
ALTER TABLE categorycombos_categories ADD INDEX fk_categorycombos_categories_categorycomboid (categorycomboid);
-- categorycombos_optioncombos table --
ALTER TABLE categorycombos_optioncombos DROP foreign KEY fk_categoryoption_categoryoptioncomboid;
	
-- categoryoptioncombos_categoryoptions table --
ALTER TABLE categorycombos_optioncombos DROP INDEX fk_categoryoption_categoryoptioncomboid;

-- chart_indicators table --
ALTER TABLE chart_indicators DROP INDEX FK21B38B45131EF72D;
ALTER TABLE chart_indicators DROP INDEX FK21B38B456D27CA40;
ALTER TABLE chart_indicators DROP INDEX FK21B38B45131EF72D;
ALTER TABLE chart_indicators ADD INDEX fk_chart_indicators_chartid (chartid);
ALTER TABLE chart_indicators ADD INDEX fk_chart_indicators_indicatorid (indicatorid);
ALTER TABLE chart_indicators DROP foreign KEY FK21B38B45131EF72D;
ALTER TABLE chart_indicators ADD CONSTRAINT fk_chart_indicators_chartid FOREIGN KEY (chartid) REFERENCES chart(chartid) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE chart_indicators DROP foreign KEY FK21B38B456D27CA40;
ALTER TABLE fk_chart_indicators_indicatorid ADD CONSTRAINT fk_chart_indicators_indicatorid FOREIGN KEY (indicatorid) REFERENCES indicator(indicatorid) ON DELETE RESTRICT ON UPDATE RESTRICT;

-- completedatasetregistration TABLE --
ALTER TABLE completedatasetregistration DROP INDEX fk_datasetcompleteregistration_sourceid;
ALTER TABLE completedatasetregistration DROP foreign KEY fk_datasetcompleteregistration_sourceid;

--  dataelement TABLE --
ALTER TABLE dataelement MODIFY shortname VARCHAR(30);
ALTER TABLE dataelement MODIFY code VARCHAR(30);
ALTER TABLE dataelement MODIFY active BIT(1) NOT NULL;
ALTER TABLE dataelement DROP INDEX fk_dataelement_extendeddataelementid;
ALTER TABLE dataelement DROP foreign KEY fk_dataelement_extendeddataelementid;
ALTER TABLE dataelement DROP COLUMN extendeddataelementid;

--  dataelementaggregationlevels TABLE --
ALTER TABLE dataelementaggregationlevels ADD INDEX fk_dataelementaggregationlevels_dataelementid (dataelementid);

-- dataelementoperand TABLE --
ALTER TABLE dataelementoperand DROP foreign KEY dataelementoperand_ibfk_1;

-- dataset TABLE --
ALTER TABLE dataset MODIFY shortname VARCHAR(30);
ALTER TABLE dataset MODIFY code VARCHAR(30);

-- datasetlocksource TABLE --
ALTER TABLE datasetlocksource DROP INDEX FK582FDF7E8FD8026A;
ALTER TABLE datasetlocksource DROP foreign KEY FK582FDF7E8FD8026A;

--  datasetsource TABLE --
ALTER TABLE datasetsource DROP INDEX FK766AE2938FD8026A;
ALTER TABLE datasetsource DROP foreign KEY FK766AE2938FD8026A;

-- datavalue TABLE --
ALTER TABLE datavalue DROP INDEX fk_datavalue_sourceid;
ALTER TABLE datavalue DROP foreign KEY fk_datavalue_sourceid;

--  document TABLE --
ALTER TABLE document MODIFY url LONGTEXT NOT NULL;
ALTER TABLE document MODIFY external BIT(1) NOT NULL;

-- indicator TABLE --
ALTER TABLE indicator MODIFY shortname VARCHAR(30);
ALTER TABLE indicator MODIFY code VARCHAR(30);
ALTER TABLE indicator DROP INDEX fk_indicator_extendeddataelementid;
ALTER TABLE indicator DROP foreign KEY fk_indicator_extendeddataelementid;
ALTER TABLE indicator DROP COLUMN extendeddataelementid;

-- maplayer TABLE --
ALTER TABLE maplayer DROP COLUMN mapsourcetype;
ALTER TABLE maplayer DROP INDEX mapsource;

-- maplayer TABLE --
ALTER TABLE maplayer MODIFY method INT(11) NOT NULL;
ALTER TABLE maplayer MODIFY classes INT(11) NOT NULL;

-- maplegendsetindicator TABLE --
ALTER TABLE maplegendsetindicator DROP INDEX FK428AED66D27CA40;
ALTER TABLE maplegendsetindicator DROP foreign KEY FK428AED66D27CA40;

-- minmaxdataelement TABLE --
ALTER TABLE minmaxdataelement MODIFY minvalue INT(11) NOT NULL;
ALTER TABLE minmaxdataelement MODIFY maxvalue INT(11) NOT NULL;
ALTER TABLE minmaxdataelement MODIFY generated BIT(1) NOT NULL;
ALTER TABLE minmaxdataelement DROP INDEX fk_minmaxdataelement_sourceid;
ALTER TABLE minmaxdataelement DROP foreign KEY fk_minmaxdataelement_sourceid;

-- organisationunit TABLE --
ALTER TABLE organisationunit MODIFY organisationunitid int(11) AUTO_INCREMENT;
ALTER TABLE organisationunit MODIFY name VARCHAR(230) NOT NULL;
ALTER TABLE organisationunit MODIFY shortname VARCHAR(30) NOT NULL;
ALTER TABLE organisationunit MODIFY code VARCHAR(30) DEFAULT NULL;
ALTER TABLE organisationunit MODIFY active BIT(1) NOT NULL;
ALTER TABLE organisationunit MODIFY name VARCHAR(230) NOT NULL;
ALTER TABLE organisationunit DROP INDEX code;
ALTER TABLE organisationunit DROP INDEX FKE509DD5EF1C932ED;
ALTER TABLE organisationunit DROP INDEX shortname;
ALTER TABLE organisationunit DROP foreign KEY FKE509DD5EF1C932ED;
SET @MAX_VALUE = (SELECT (MAX(organisationunitid) + 1) FROM organisationunit) ;
set @qry = ( SELECT concat('ALTER TABLE organisationunit AUTO_INCREMENT = ',@MAX_VALUE,';') FROM organisationunit LIMIT 1);
prepare stmt from @qry; execute stmt;

-- orgunitgroup TABLE --
ALTER TABLE orgunitgroup MODIFY name VARCHAR(230);

-- orgunitgroupset TABLE --
ALTER TABLE orgunitgroup MODIFY name VARCHAR(230);
ALTER TABLE orgunitgroup DROP COLUMN exclusive;

-- patientattribute TABLE --
ALTER TABLE patientattribute MODIFY mandatory BIT(1) NOT NULL;
ALTER TABLE patientattribute MODIFY inheritable BIT(1) DEFAULT NULL;

-- patientdatavaluearchive TABLE --
ALTER TABLE patientdatavaluearchive MODIFY `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

--  patientidentifier TABLE --
ALTER TABLE patientidentifier DROP INDEX FK9D2A556EFB4CAAAD;
ALTER TABLE patientidentifier DROP foreign KEY FK9D2A556E49CD44E2;
ALTER TABLE patientidentifier DROP foreign KEY FK9D2A556EFB4CAAAD;
ALTER TABLE patientidentifier DROP COLUMN organisationunitid;

--  periodtype TABLE --
ALTER TABLE periodtype MODIFY name VARCHAR(50);

--  program TABLE --
ALTER TABLE program MODIFY dateOfEnrollmentDescription LONGTEXT NOT NULL;
ALTER TABLE program MODIFY dateOfIncidentDescription LONGTEXT NOT NULL;

-- programstage TABLE --
ALTER TABLE programstage MODIFY stageinprogram INT(11) NOT NULL;
ALTER TABLE programstage MODIFY mindaysfromstart INT(11) NOT NULL;
ALTER TABLE programstage DROP INDEX FK4CFE16FAA3100C9F;

-- programstageinstance TABLE --
ALTER TABLE programstageinstance MODIFY stageinprogram INT(11) NOT NULL;

-- programstage_dataelements TABLE --
ALTER TABLE programstage_dataelements MODIFY compulsory BIT(1) NOT NULL;
ALTER TABLE programstage_dataelements ADD COLUMN sort_order INT(11) DEFAULT NULL;
ALTER TABLE programstage_dataelements ADD CONSTRAINT fk_programstagedataelement_dataelementid FOREIGN KEY (dataelementid) REFERENCES dataelement(dataelementid) ON DELETE RESTRICT ON UPDATE RESTRICT;
	
-- program_criteria TABLE --
ALTER TABLE program_criteria ADD INDEX fk_program_criteria_programid (programid);

-- report TABLE --
ALTER TABLE report DROP COLUMN design;
ALTER TABLE report DROP COLUMN type;

-- section TABLE --
ALTER TABLE section MODIFY name VARCHAR(255);
ALTER TABLE section MODIFY datasetid INT(11) DEFAULT NULL;
ALTER TABLE section MODIFY sortorder INT(11) NOT NULL;
ALTER TABLE programstage DROP foreign KEY section_ibfk_1;

-- translation TABLE --
ALTER TABLE translation MODIFY value LONGTEXT NOT NULL DEFAULT '';

-- userinfo TABLE --
ALTER TABLE userinfo CHANGE COLUMN firstName firstname VARCHAR(160);

-- userroledataset TABLE --
ALTER TABLE userroledataset DROP INDEX fk_datasetid;
ALTER TABLE userroledataset DROP INDEX FK27213A97B2EB236C;
ALTER TABLE userroledataset ADD CONSTRAINT fk_userroledataset_datasetid FOREIGN KEY (datasetid)
    REFERENCES dataset(datasetid) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE userroledataset ADD CONSTRAINT fk_userroledataset_userroleid FOREIGN KEY (userroleid)
    REFERENCES userrole(userroleid) ON DELETE RESTRICT ON UPDATE RESTRICT;
	
-- INDIA module --
--alter table linelistsource drop FOREIGN key  FK75F5F92D8FD8026A;
--alter table lldatavalue drop FOREIGN key  fk_lldatavalue_sourceid;
--alter table reportsource drop FOREIGN key  FK5A4D064F8FD8026A;
--alter table surveysource drop FOREIGN key  fk_survey_sourceid;

-- DROP TABLE --
DROP TABLE caseaggregation;
DROP TABLE compulsorydatasetmembers;
DROP TABLE extendeddataelement;
DROP TABLE `source`;


