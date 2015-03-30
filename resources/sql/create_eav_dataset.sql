DROP TYPE IF EXISTS eav_text CASCADE;
CREATE TYPE eav_text AS (objectid bigint, attribute text, "value" text);

-- Sequence: datavalueid

-- DROP SEQUENCE datavalueid;

CREATE SEQUENCE datavalueid
  INCREMENT 1
  MINVALUE 1
  MAXVALUE 9223372036854775807
  START 2830543
  CACHE 1;
ALTER TABLE datavalueid OWNER TO postgres;



-- Function: create_eav_datavalue(integer, integer, integer, integer)

-- DROP FUNCTION create_eav_datavalue(integer, integer, integer, integer);

CREATE OR REPLACE FUNCTION create_eav_datavalue(mydataelementid integer, myperiodid integer, mysourceid integer, mycategoryoptioncomboid integer)
  RETURNS SETOF eav_text AS
$BODY$

DECLARE
this_objectid bigint DEFAULT 0;
rec record;
total_records integer DEFAULT 0;


BEGIN
this_objectid := 1;
FOR rec in ( SELECT COUNT(value) as myvalue, nextval('datavalueid'::regclass) as myobjectid FROM datavalue 
 where  dataelementid = mydataelementid
 AND periodid = myperiodid AND sourceid = mysourceid AND 
 categoryoptioncomboid = mycategoryoptioncomboid)
 LOOP
 total_records := rec.myvalue;
 this_objectid := rec.myobjectid;
 END LOOP;



 IF total_records = 1 THEN
FOR rec in (
SELECT this_objectid, 'dataelementname'::text, "name"::text
 FROM dataelement where dataelementid = mydataelementid
UNION
SELECT this_objectid, 'startdate'::text, startdate::text
 FROM period where periodid = myperiodid
 UNION
SELECT this_objectid, 'enddatte'::text, enddate::text
 FROM period where periodid = myperiodid
UNION
SELECT this_objectid, 'orgunitname'::text, "name"::text
FROM organisationunit where organisationunitid = mysourceid
UNION
SELECT this_objectid, 'value'::text, "value"::text
FROM datavalue where sourceid = mysourceid
AND periodid = myperiodid AND dataelementid = mydataelementid 
AND categoryoptioncomboid = mycategoryoptioncomboid
UNION
SELECT this_objectid, dataelementcategory.name, dataelementcategoryoption.name FROM categories_categoryoptions
INNER JOIN dataelementcategory ON dataelementcategory.categoryid = categories_categoryoptions.categoryid
INNER JOIN dataelementcategoryoption ON  dataelementcategoryoption.categoryoptionid = categories_categoryoptions.categoryoptionid
WHERE categories_categoryoptions.categoryoptionid IN
(SELECT categoryoptionid FROM categoryoptioncombos_categoryoptions where categoryoptioncomboid = mycategoryoptioncomboid  ))


  LOOP
 RETURN NEXT rec;
 END LOOP;

 ELSE
 END IF;


END;


  $BODY$
  LANGUAGE 'plpgsql' VOLATILE
  COST 100
  ROWS 1;
ALTER FUNCTION create_eav_datavalue(integer, integer, integer, integer) OWNER TO postgres;


-- Function: create_eav_orgunit(integer)

-- DROP FUNCTION create_eav_orgunit(integer);

CREATE OR REPLACE FUNCTION create_eav_orgunit(mysourceid integer)
  RETURNS integer AS
$BODY$

DECLARE
periods record;
dataelements record;
catoptions record;

BEGIN

 EXECUTE 'DROP TABLE IF EXISTS _eav_dataset_' || mysourceid::text;
 EXECUTE 'CREATE TABLE _eav_dataset_'
 || mysourceid::text 
 ||'( objectid integer, attribute text, "value" text)';


FOR periods in 
 SELECT DISTINCT periodid from datavalue where sourceid = mysourceid LOOP
   FOR dataelements in 
      SELECT DISTINCT dataelementid from datavalue where sourceid = mysourceid AND periodid = periods.periodid LOOP
      
          FOR catoptions IN 
          SELECT DISTINCT categoryoptioncomboid from datavalue where 
                 dataelementid = dataelements.dataelementid
                 AND sourceid = mysourceid
                 AND periodid = periods.periodid LOOP 

                 EXECUTE '
                 INSERT INTO _eav_dataset_' 
                 || mysourceid::text 
                 || '(objectid, attribute, "value")
		 SELECT * FROM
		  create_eav_datavalue('
		 || dataelements.dataelementid
		 || ','
		 || periods.periodid
		 || ',' 
		 || mysourceid
		 || ',' 
		 || catoptions.categoryoptioncomboid
		 || ')';
	END LOOP;
	END LOOP;
	END LOOP;
                
  RETURN 1;     

END;


  $BODY$
  LANGUAGE 'plpgsql' VOLATILE
  COST 100;
ALTER FUNCTION create_eav_orgunit(integer) OWNER TO postgres;

