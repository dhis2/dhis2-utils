drop index aggregateddatavalue_index;
drop index aggregatedindicatorvalue_index;
drop index aggregateddatasetcompleteness_index;
drop index aggregatedorgunitdatavalue_index;
drop index aggregatedorgunitindicatorvalue_index;

CREATE INDEX aggregateddatavalue_index ON aggregateddatavalue (dataelementid, categoryoptioncomboid, periodid, organisationunitid);
CREATE INDEX aggregatedindicatorvalue_index ON aggregatedindicatorvalue (indicatorid, periodid, organisationunitid);
CREATE INDEX aggregateddatasetcompleteness_index ON aggregateddatasetcompleteness (datasetid, periodid, organisationunitid);
CREATE INDEX aggregatedorgunitdatavalue_index  ON aggregatedorgunitdatavalue (dataelementid, categoryoptioncomboid, periodid, organisationunitid, organisationunitgroupid);
CREATE INDEX aggregatedorgunitindicatorvalue_index ON aggregatedorgunitindicatorvalue (indicatorid, periodid, organisationunitid, organisationunitgroupid);
