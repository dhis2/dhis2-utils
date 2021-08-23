CREATE FUNCTION UpdateDataAGGDate (period_type text) RETURNS boolean
    LANGUAGE plpgsql
AS
$$
DECLARE
BEGIN

    WITH tbl_shift_date as 
    (
        SELECT 
        dataelementid,
        sourceid,
        categoryoptioncomboid,
        attributeoptioncomboid,
        value,
        dv.periodid as old_periodid,
        pt.name as frequency,
        pp.periodtypeid, pp.startdate,
        CASE WHEN pp.periodtypeid=1 THEN DATE(pp.startdate + INTERVAL '1 DAY') -- Daily
             WHEN pp.periodtypeid=2 THEN DATE(pp.startdate + INTERVAL '7 DAY') -- Weekly
             WHEN pp.periodtypeid=8 THEN DATE(date_trunc('month', pp.startdate + INTERVAL '1 MONTH')) -- Monthly
             WHEN pp.periodtypeid=10 THEN DATE(date_trunc('quarter', pp.startdate + INTERVAL '3 MONTH')) -- Quarterly
             WHEN pp.periodtypeid=14 THEN DATE(date_trunc('year', pp.startdate + INTERVAL '1 YEAR')) -- Yearly
        END as new_date
        FROM datavalue dv 
        LEFT JOIN period pp on dv.periodid = pp.periodid
        LEFT JOIN periodtype pt on pp.periodtypeid = pt.periodtypeid
        ORDER BY pp.startdate DESC
    )
    SELECT dv.dataelementid, dv.sourceid, dv.categoryoptioncomboid, dv.attributeoptioncomboid, dv.value, tbl_shift_date.old_periodid, tbl_shift_date.startdate, new_period.periodid, new_period.startdate
    FROM tbl_shift_date
    INNER JOIN datavalue dv ON
        dv.dataelementid = tbl_shift_date.dataelementid AND
        dv.sourceid = tbl_shift_date.sourceid AND
        dv.categoryoptioncomboid = tbl_shift_date.categoryoptioncomboid AND
        dv.attributeoptioncomboid = tbl_shift_date.attributeoptioncomboid AND
        dv.value = tbl_shift_date.value AND -- Not part of the unique key
        dv.periodid = tbl_shift_date.old_periodid
    INNER JOIN period new_period on tbl_shift_date.periodtypeid = new_period.periodtypeid AND new_period.startdate = tbl_shift_date.new_date
    WHERE
        tbl_shift_date.frequency = period_type;

    RETURN TRUE;
END
$$;