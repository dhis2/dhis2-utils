-- Function: create_ct_source_period(integer)

-- DROP FUNCTION create_ct_source_period(integer);

CREATE OR REPLACE FUNCTION create_ct_source_period(mydataelementid integer)
  RETURNS integer AS
$BODY$
DECLARE

categoryoptioncombos record;
rec record;

BEGIN
--drop the existing table if it exists
EXECUTE 'DROP TABLE IF EXISTS _ct_source_period_' || mydataelementid ;
--create the table again with the appropriate columns
EXECUTE ' CREATE TABLE _ct_source_period_' || mydataelementid ||' (
  periodid integer NOT NULL,
  sourceid integer NOT NULL,
  CONSTRAINT _ct_source_period_' ||mydataelementid || '_pkey PRIMARY KEY (periodid, sourceid)
  )';
  
FOR categoryoptioncombos in 
	SELECT DISTINCT categoryoptioncomboid
	 FROM categorycombos_optioncombos WHERE categorycomboid = (SELECT 
	 categorycomboid FROM dataelement where dataelementid = mydataelementid LIMIT 1) 
	 ORDER BY categoryoptioncomboid LOOP
	 EXECUTE 'ALTER TABLE _ct_source_period_' 
	 || mydataelementid 
	 || ' ADD COLUMN de_'
	 || mydataelementid 
	 || '_'
	 || categoryoptioncombos.categoryoptioncomboid
	 || ' character varying(255)';
	 END LOOP;
	 
--insert all the possible source, periodids for this dataelement, sourceid, and periodid
	 EXECUTE 'INSERT INTO _ct_source_period_'
	  || mydataelementid
	  || '(sourceid, periodid)'
	  || 'SELECT DISTINCT sourceid, periodid from datavalue'
	  || ' WHERE dataelementid = ' || mydataelementid;
--start updating each column in turn from the datavalue table
FOR categoryoptioncombos in 
	SELECT DISTINCT categoryoptioncomboid
	 FROM categorycombos_optioncombos WHERE categorycomboid = (SELECT 
	 categorycomboid FROM dataelement where dataelementid = mydataelementid LIMIT 1) 
	 ORDER BY categoryoptioncomboid LOOP
         EXECUTE 'UPDATE _ct_source_period_'
	  || mydataelementid || ' mytable'
	  || ' SET de_' || mydataelementid || '_' || categoryoptioncombos.categoryoptioncomboid
	  || ' = dv.value from datavalue dv'
	  || ' WHERE dv.dataelementid = ' 
	  || mydataelementid
	  || ' AND mytable.sourceid = dv.sourceid'
	  || ' AND mytable.periodid = dv.periodid'
	  || ' AND dv.categoryoptioncomboid = ' || categoryoptioncombos.categoryoptioncomboid;
	 END LOOP;
	 




	 
RETURN 1;
END;
$BODY$
  LANGUAGE 'plpgsql' VOLATILE
  COST 100;
ALTER FUNCTION create_ct_source_period(integer) OWNER TO postgres;

