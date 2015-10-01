CREATE OR REPLACE FUNCTION merge_organisationunits(source_uid character(11),dest_uid character(11)) RETURNS integer AS $$
DECLARE
organisationunitid integer;
has_children boolean;
BEGIN

EXECUTE 'SELECT organisationunitid from organisationunit where uid = ''' ||   $1  || ''''  INTO organisationunitid;

EXECUTE 'SELECT COUNT(organisationunitid) != 0 from organisationunit where parentid = $1' INTO has_children USING organisationunitid;

IF  has_children THEN
RAISE EXCEPTION 'Organisationunit has children. Aborting.';
END IF;




-- All overlapping data, only of valuetype INT
EXECUTE format('CREATE TEMP TABLE _temp_merge_overlaps  ON COMMIT DROP AS SELECT a.*  FROM datavalue a
INNER JOIN
(SELECT dataelementid,periodid,categoryoptioncomboid,attributeoptioncomboid,COUNT(*) from datavalue
WHERE sourceid in (
select organisationunitid from organisationunit  where uid IN ( %L,%L ) )
GROUP BY dataelementid,periodid,categoryoptioncomboid,attributeoptioncomboid
HAVING COUNT(*) > 1)  b on
a.dataelementid = b.dataelementid
AND
a.periodid = b.periodid
AND
a.categoryoptioncomboid = b.categoryoptioncomboid
AND
a.attributeoptioncomboid = b.attributeoptioncomboid
WHERE a.sourceid IN (
select organisationunitid from organisationunit
where uid IN ( %L,%L) )
and a.dataelementid in (SELECT DISTINCT dataelementid from dataelement where valuetype = ''int'')',
source_uid,dest_uid,source_uid,dest_uid);


--Switch the source 
EXECUTE format('UPDATE _temp_merge_overlaps set sourceid = 
(select organisationunitid from organisationunit where uid =  %L )',dest_uid);



--Audit the changes about to be made to the overlapping data

INSERT INTO datavalueaudit SELECT nextval('hibernate_sequence'::regclass),
a.dataelementid,
a.periodid,
a.sourceid as organisationunitid,
a.categoryoptioncomboid,
a.value,
now()::timestamp without time zone,
'admin'::character varying(100) as modifiedby,
'DELETE'::character varying(255) as audittype,
a.attributeoptioncomboid
FROM datavalue a
INNER JOIN
(SELECT DISTINCT sourceid,dataelementid,categoryoptioncomboid,
	attributeoptioncomboid,periodid from _temp_merge_overlaps) b
ON a.sourceid = b.sourceid
and a.dataelementid = b.dataelementid
and a.categoryoptioncomboid = b.categoryoptioncomboid
and a.attributeoptioncomboid = b.attributeoptioncomboid
and a.periodid = b.periodid;

--UPDATE the overlapping data

UPDATE datavalue a set value = b.value from (
SELECT sourceid,dataelementid,periodid,categoryoptioncomboid,attributeoptioncomboid,
SUM(value::numeric)::character varying(50000) as value FROM _temp_merge_overlaps
GROUP BY sourceid,dataelementid,periodid,categoryoptioncomboid,attributeoptioncomboid) b
WHERE a.sourceid = b.sourceid
AND a.dataelementid = b.dataelementid
and a.categoryoptioncomboid = b.categoryoptioncomboid
and a.attributeoptioncomboid = b.attributeoptioncomboid;


--New records from the source which do not overlap at all
EXECUTE format('UPDATE datavalue AS d1 SET sourceid=(select organisationunitid 
	from organisationunit where uid = %L) 
WHERE sourceid=(select organisationunitid from organisationunit where uid = %L )
AND NOT EXISTS (SELECT * from datavalue AS d2 
WHERE d2.sourceid=(select organisationunitid from organisationunit where uid = %L ) 
AND d1.dataelementid=d2.dataelementid
AND d1.periodid=d2.periodid 
AND d1.categoryoptioncomboid=d2.categoryoptioncomboid 
AND d1.attributeoptioncomboid=d2.attributeoptioncomboid)',dest_uid,source_uid,dest_uid);


--Audit the changes to be made to the source data as it will be totally removed in the next step.
EXECUTE format('INSERT INTO datavalueaudit SELECT nextval(''hibernate_sequence''::regclass),
dataelementid,
periodid,
( SELECT organisationunitid from organisationunit where uid = %L ) as organisationunitid,
categoryoptioncomboid,
value,
now()::timestamp without time zone,
''admin''::character varying(100) as modifiedby,
''MERGE_SOURCE''::character varying(255) as audittype,
attributeoptioncomboid
FROM datavalue where sourceid = ( SELECT organisationunitid 
	from organisationunit where uid = %L )',dest_uid,source_uid);

--Switch all datavalue audit records for the unit to be removed
EXECUTE format('UPDATE datavalueaudit set organisationunitid = 
(SELECT organisationunitid from organisationunit where uid = %L )
WHERE organisationunitid = (select organisationunitid 
	from organisationunit where uid = %L )',dest_uid,source_uid);

--DELETE all records for the source
EXECUTE format('SELECT * FROM delete_site_with_data( %L )',source_uid);


RETURN 1;

END;
$$ LANGUAGE plpgsql VOLATILE;
