CREATE OR REPLACE FUNCTION delete_orgunittree_with_data(uid character(11)) RETURNS integer AS $$
DECLARE
organisationunitid integer;
resort_object RECORD;
resort_integer integer;

BEGIN

EXECUTE 'SELECT organisationunitid from organisationunit where uid = ''' ||   $1  || ''''  INTO organisationunitid;

EXECUTE 'SELECT delete_orgunittree_with_data(uid) from organisationunit where parentid = $1' USING organisationunitid;

EXECUTE 'DELETE FROM completedatasetregistration where sourceid = $1' USING organisationunitid;
EXECUTE 'DELETE FROM datavalueaudit where organisationunitid = $1' USING organisationunitid;
EXECUTE 'DELETE FROM datavalue where sourceid = $1' USING organisationunitid;
EXECUTE 'DELETE FROM dataapproval where organisationunitid = $1' USING organisationunitid;
EXECUTE 'DELETE FROM datasetsource WHERE sourceid = $1 ' USING organisationunitid;
EXECUTE 'DELETE FROM organisationunitattributevalues WHERE organisationunitid = $1 ' USING organisationunitid;
EXECUTE 'DELETE FROM categoryoption_organisationunits WHERE organisationunitid = $1 ' USING organisationunitid;
EXECUTE 'DELETE FROM interpretation WHERE organisationunitid = $1 ' USING organisationunitid;
EXECUTE 'DELETE FROM lockexception WHERE organisationunitid = $1 ' USING organisationunitid;
EXECUTE 'DELETE FROM minmaxdataelement WHERE sourceid = $1 ' USING organisationunitid;
EXECUTE 'DELETE FROM orgunitgroupmembers WHERE organisationunitid = $1 ' USING organisationunitid;

--delete all data from programstageinstance and down based on first programstageinstance orgunit then programinstance orgunit and lastly trackedentityinstance orgunit
EXECUTE 'DELETE FROM trackedentitydatavalueaudit WHERE programstageinstanceid IN (SELECT programstageinstanceid FROM programstageinstance WHERE organisationunitid = $1 OR programinstanceid IN (SELECT programinstanceid FROM programinstance WHERE organisationunitid = $1 OR trackedentityinstanceid IN (SELECT trackedentityinstanceid FROM trackedentityinstance WHERE organisationunitid = $1))) '
USING organisationunitid;
EXECUTE 'DELETE FROM programstageinstancecomments WHERE programstageinstanceid IN (SELECT programstageinstanceid FROM programstageinstance WHERE organisationunitid = $1 OR programinstanceid IN (SELECT programinstanceid FROM programinstance WHERE organisationunitid = $1 OR trackedentityinstanceid IN (SELECT trackedentityinstanceid FROM trackedentityinstance WHERE organisationunitid = $1))) '
USING organisationunitid;
EXECUTE 'DELETE FROM programstageinstance_outboundsms WHERE programstageinstanceid IN (SELECT programstageinstanceid FROM programstageinstance WHERE organisationunitid = $1 OR programinstanceid IN (SELECT programinstanceid FROM programinstance WHERE organisationunitid = $1 OR trackedentityinstanceid IN (SELECT trackedentityinstanceid FROM trackedentityinstance WHERE organisationunitid = $1))) '
USING organisationunitid;
EXECUTE 'DELETE FROM programstageinstance WHERE programstageinstanceid IN (SELECT programstageinstanceid FROM programstageinstance WHERE organisationunitid = $1 OR programinstanceid IN (SELECT programinstanceid FROM programinstance WHERE organisationunitid = $1 OR trackedentityinstanceid IN (SELECT trackedentityinstanceid FROM trackedentityinstance WHERE organisationunitid = $1))) '
USING organisationunitid;

--delete all programinstances based on first programinstance orgunit then tracked entity instance orgunit
EXECUTE 'DELETE FROM programinstancecomments WHERE programinstanceid in (SELECT programinstanceid FROM programinstance WHERE organisationunitid = $1 OR trackedentityinstanceid IN (SELECT trackedentityinstanceid FROM trackedentityinstance WHERE organisationunitid = $1 )) ' USING organisationunitid;
EXECUTE 'DELETE FROM programinstance WHERE organisationunitid = $1 OR trackedentityinstanceid IN (SELECT trackedentityinstanceid FROM trackedentityinstance WHERE organisationunitid = $1 ) ' USING organisationunitid;

--delete all data still connected to trackedentityinstances based on trackedentityinstance orgunit
EXECUTE 'DELETE FROM trackedentityattributevalue WHERE trackedentityinstanceid IN(SELECT trackedentityinstanceid from trackedentityinstance where organisationunitid = $1) ' USING organisationunitid;
EXECUTE 'DELETE FROM trackedentityattributevalueaudit WHERE trackedentityinstanceid IN(SELECT trackedentityinstanceid from trackedentityinstance where organisationunitid = $1) ' USING organisationunitid;
EXECUTE 'DELETE FROM trackedentityinstance WHERE organisationunitid = $1 ' USING organisationunitid;

EXECUTE 'DELETE FROM userdatavieworgunits WHERE organisationunitid = $1 ' USING organisationunitid;
EXECUTE 'DELETE FROM program_organisationunits WHERE organisationunitid = $1 ' USING organisationunitid;
EXECUTE 'DELETE FROM usermembership where organisationunitid = $1' USING organisationunitid;
--Special tables which we need to reorder the sort order after deletion of the organisationunit

SET client_min_messages=WARNING;

CREATE TEMP TABLE IF NOT EXISTS temp1 (
   objectid integer ) ON COMMIT DROP;

--chart_organisationunits
EXECUTE 'DELETE FROM chart_organisationunits WHERE organisationunitid = $1 ' USING organisationunitid;
EXECUTE 'INSERT INTO temp1 SELECT chartid from chart_organisationunits where organisationunitid = $1 'USING organisationunitid;

FOR resort_object IN SELECT objectid from temp1 LOOP
EXECUTE 'update chart_organisationunits set sort_order = -t.i
from (select row_number() over (ORDER BY sort_order) as i, chartid, sort_order, organisationunitid
   from chart_organisationunits where chartid=$1 order by sort_order) t
where chart_organisationunits.organisationunitid = t.organisationunitid and chart_organisationunits.chartid=$1' USING resort_object.objectid ;
EXECUTE 'update chart_organisationunits set sort_order = -(sort_order+1) where chartid=$1' USING resort_object.objectid ;
END LOOP;
EXECUTE 'TRUNCATE temp1';

--reporttable_organisationunits

EXECUTE 'INSERT INTO temp1 SELECT DISTINCT reporttableid from reporttable_organisationunits where organisationunitid = $1 'USING organisationunitid;
EXECUTE 'DELETE FROM reporttable_organisationunits WHERE organisationunitid = $1 ' USING organisationunitid;

FOR resort_object IN SELECT objectid from temp1 LOOP
EXECUTE 'update reporttable_organisationunits set sort_order = -t.i
from (select row_number() over (ORDER BY sort_order) as i, reporttableid, sort_order, organisationunitid
from reporttable_organisationunits where reporttableid=$1 order by sort_order) t
where reporttable_organisationunits.organisationunitid = t.organisationunitid and reporttable_organisationunits.reporttableid=$1' USING resort_object.objectid ;
EXECUTE 'update reporttable_organisationunits set sort_order = -(sort_order+1) where reporttableid=$1' USING resort_object.objectid ;

END LOOP;
EXECUTE 'TRUNCATE temp1';

--mapview_organisationunits

EXECUTE 'INSERT INTO temp1 SELECT DISTINCT mapviewid from mapview_organisationunits where organisationunitid = $1 'USING organisationunitid;
EXECUTE 'DELETE FROM mapview_organisationunits WHERE organisationunitid = $1 ' USING organisationunitid;
FOR resort_object IN SELECT objectid from temp1 LOOP
EXECUTE 'update mapview_organisationunits set sort_order = -t.i
from (select row_number() over (ORDER BY sort_order) as i,mapviewid, sort_order, organisationunitid
from mapview_organisationunits where mapviewid=$1 order by sort_order) t
where mapview_organisationunits.organisationunitid = t.organisationunitid and mapview_organisationunits.mapviewid=$1' USING resort_object.objectid ;
EXECUTE 'update mapview_organisationunits set sort_order = -(sort_order+1) where mapviewid=$1' USING resort_object.objectid ;
END LOOP;
EXECUTE 'TRUNCATE temp1';

-- eventchart_organisationunits

EXECUTE 'INSERT INTO temp1 SELECT DISTINCT eventchartid from eventchart_organisationunits where organisationunitid = $1 'USING organisationunitid;
EXECUTE 'DELETE FROM eventchart_organisationunits WHERE organisationunitid = $1 ' USING organisationunitid;

FOR resort_object IN SELECT objectid from temp1 LOOP
EXECUTE 'update eventchart_organisationunits set sort_order = -t.i
from (select row_number() over (ORDER BY sort_order) as i, eventchartid, sort_order, organisationunitid
    from eventchart_organisationunits where eventchartid=$1 order by sort_order) t
where eventchart_organisationunits.organisationunitid = t.organisationunitid and eventchart_organisationunits.eventchartid=$1' USING resort_object.objectid ;
EXECUTE 'update eventchart_organisationunits set sort_order = -(sort_order+1) where eventchartid=$1' USING resort_object.objectid ;
END LOOP;
EXECUTE 'TRUNCATE temp1';

-- eventchart_organisationunits

EXECUTE 'INSERT INTO temp1 SELECT DISTINCT eventreportid from eventreport_organisationunits where organisationunitid = $1 'USING organisationunitid;
EXECUTE 'DELETE FROM eventreport_organisationunits WHERE organisationunitid = $1 ' USING organisationunitid;
FOR resort_object IN SELECT objectid from temp1 LOOP
EXECUTE 'UPDATE eventreport_organisationunits set sort_order = -t.i
from (select row_number() over (ORDER BY sort_order) as i, eventreportid, sort_order, organisationunitid
    from eventreport_organisationunits where eventreportid=$1 order by sort_order) t
where eventreport_organisationunits.organisationunitid = t.organisationunitid and eventreport_organisationunits.eventreportid=$1' USING resort_object.objectid ;
EXECUTE 'update eventreport_organisationunits set sort_order = -(sort_order+1) where eventreportid=$1' USING resort_object.objectid ;
END LOOP;
EXECUTE 'TRUNCATE temp1';

EXECUTE 'DELETE FROM organisationunittranslations WHERE organisationunitid = $1 ' USING organisationunitid;

EXECUTE 'DELETE FROM organisationunit WHERE organisationunitid = $1 ' USING organisationunitid;

RETURN 1;

END;
$$ LANGUAGE plpgsql VOLATILE;
