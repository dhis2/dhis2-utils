CREATE OR REPLACE FUNCTION merge_organisationunits(source_uid character(11),dest_uid character(10),strategy character varying(50)) RETURNS integer AS $$
DECLARE
organisationunitid integer;
has_children boolean;
is_valid_strategy boolean;
BEGIN

EXECUTE 'SELECT' || '''' || $3 || ''' NOT IN (''SUM'',''MAX'',''MIN'',''AVG'',''LAST'',''FIRST'')' INTO is_valid_strategy USING strategy;

IF is_valid_strategy  THEN
RAISE EXCEPTION 'Please provide a merge strategy (SUM,MAX,MIN,AVG,LAST,FIRST)';
END IF;


EXECUTE 'SELECT organisationunitid from organisationunit where uid = ''' ||   $1  || ''''  INTO organisationunitid;

EXECUTE 'SELECT COUNT(organisationunitid) != 0 from organisationunit where parentid = $1' INTO has_children USING organisationunitid;

IF  has_children THEN
RAISE EXCEPTION 'Organisationunit has children. Aborting.';
END IF;


-- All overlapping data, only of valuetype INT
EXECUTE format('CREATE TEMP TABLE _temp_merge_overlaps  ON COMMIT DROP AS
 SELECT a.*  FROM datavalue a
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



--UPDATE the overlapping INT data
CASE  strategy WHEN 'SUM' THEN
UPDATE datavalue a set value = b.value from (
SELECT sourceid,dataelementid,periodid,categoryoptioncomboid,attributeoptioncomboid,
SUM(value::numeric)::character varying(50000) as value FROM _temp_merge_overlaps
GROUP BY sourceid,dataelementid,periodid,categoryoptioncomboid,attributeoptioncomboid) b
WHERE a.sourceid = b.sourceid
AND a.dataelementid = b.dataelementid
and a.categoryoptioncomboid = b.categoryoptioncomboid
and a.attributeoptioncomboid = b.attributeoptioncomboid;
 WHEN 'AVG' THEN
UPDATE datavalue a set value = b.value from (
SELECT sourceid,dataelementid,periodid,categoryoptioncomboid,attributeoptioncomboid,
AVG(value::numeric)::integer::character varying(50000) as value FROM _temp_merge_overlaps
GROUP BY sourceid,dataelementid,periodid,categoryoptioncomboid,attributeoptioncomboid) b
WHERE a.sourceid = b.sourceid
AND a.dataelementid = b.dataelementid
and a.categoryoptioncomboid = b.categoryoptioncomboid
and a.attributeoptioncomboid = b.attributeoptioncomboid;
 WHEN 'MAX' THEN
UPDATE datavalue a set value = b.value from (
SELECT sourceid,dataelementid,periodid,categoryoptioncomboid,attributeoptioncomboid,
MAX(value::numeric)::integer::character varying(50000) as value FROM _temp_merge_overlaps
GROUP BY sourceid,dataelementid,periodid,categoryoptioncomboid,attributeoptioncomboid) b
WHERE a.sourceid = b.sourceid
AND a.dataelementid = b.dataelementid
and a.categoryoptioncomboid = b.categoryoptioncomboid
and a.attributeoptioncomboid = b.attributeoptioncomboid;
WHEN 'MIN' THEN
UPDATE datavalue a set value = b.value from (
SELECT sourceid,dataelementid,periodid,categoryoptioncomboid,attributeoptioncomboid,
MIN(value::numeric)::integer::character varying(50000) as value FROM _temp_merge_overlaps
GROUP BY sourceid,dataelementid,periodid,categoryoptioncomboid,attributeoptioncomboid) b
WHERE a.sourceid = b.sourceid
AND a.dataelementid = b.dataelementid
and a.categoryoptioncomboid = b.categoryoptioncomboid
and a.attributeoptioncomboid = b.attributeoptioncomboid;
WHEN 'LAST' THEN
UPDATE datavalue a set value = b.value from (
SELECT x.sourceid,x.dataelementid,x.periodid,x.categoryoptioncomboid,x.attributeoptioncomboid,
x.value as value FROM _temp_merge_overlaps x
INNER  JOIN (
SELECT sourceid,dataelementid,periodid,categoryoptioncomboid,attributeoptioncomboid,
MIN(lastupdated) as lastupdated from _temp_merge_overlaps
GROUP BY sourceid,dataelementid,periodid,categoryoptioncomboid,attributeoptioncomboid
) y on
x.sourceid = y.sourceid
AND x.dataelementid = y.dataelementid
and x.categoryoptioncomboid = y.categoryoptioncomboid
and x.attributeoptioncomboid = y.attributeoptioncomboid
and x.lastupdated = y.lastupdated) b
WHERE a.sourceid = b.sourceid
AND a.dataelementid = b.dataelementid
and a.categoryoptioncomboid = b.categoryoptioncomboid
and a.attributeoptioncomboid = b.attributeoptioncomboid;
WHEN 'FIRST' THEN
UPDATE datavalue a set value = b.value from (
SELECT x.sourceid,x.dataelementid,x.periodid,x.categoryoptioncomboid,x.attributeoptioncomboid,
x.value as value FROM _temp_merge_overlaps x
INNER  JOIN (
SELECT sourceid,dataelementid,periodid,categoryoptioncomboid,attributeoptioncomboid,
MAX(lastupdated) as lastupdated from _temp_merge_overlaps
GROUP BY sourceid,dataelementid,periodid,categoryoptioncomboid,attributeoptioncomboid
) y on
x.sourceid = y.sourceid
AND x.dataelementid = y.dataelementid
and x.categoryoptioncomboid = y.categoryoptioncomboid
and x.attributeoptioncomboid = y.attributeoptioncomboid
and x.lastupdated = y.lastupdated) b
WHERE a.sourceid = b.sourceid
AND a.dataelementid = b.dataelementid
and a.categoryoptioncomboid = b.categoryoptioncomboid
and a.attributeoptioncomboid = b.attributeoptioncomboid;
END CASE;

-- All overlapping data of anything other than INT
EXECUTE format('CREATE TEMP TABLE _temp_merge_overlaps_others  ON COMMIT DROP AS
 SELECT a.*  FROM datavalue a
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
and a.dataelementid in (SELECT DISTINCT dataelementid from dataelement where valuetype != ''int'')',
source_uid,dest_uid,source_uid,dest_uid);

--Switch the source 
EXECUTE format('UPDATE _temp_merge_overlaps_others set sourceid = 
(select organisationunitid from organisationunit where uid =  %L )',dest_uid);

UPDATE datavalue a set value = b.value from (
SELECT x.sourceid,x.dataelementid,x.periodid,x.categoryoptioncomboid,x.attributeoptioncomboid,
x.value as value FROM _temp_merge_overlaps_others x
INNER  JOIN (
SELECT sourceid,dataelementid,periodid,categoryoptioncomboid,attributeoptioncomboid,
MIN(lastupdated) as lastupdated from _temp_merge_overlaps_others
GROUP BY sourceid,dataelementid,periodid,categoryoptioncomboid,attributeoptioncomboid
) y on
x.sourceid = y.sourceid
AND x.dataelementid = y.dataelementid
and x.categoryoptioncomboid = y.categoryoptioncomboid
and x.attributeoptioncomboid = y.attributeoptioncomboid
and x.lastupdated = y.lastupdated) b
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
