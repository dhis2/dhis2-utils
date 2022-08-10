CREATE OR REPLACE FUNCTION UpdateDataAGGDate (period_type text) RETURNS boolean
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
        CASE WHEN pt.name = 'Daily' THEN DATE(pp.startdate + INTERVAL '1 DAY')
             WHEN pt.name = 'Weekly' THEN DATE(pp.startdate + INTERVAL '7 DAY')
             WHEN pt.name = 'Monthly' THEN DATE(date_trunc('month', pp.startdate + INTERVAL '1 MONTH'))
             WHEN pt.name = 'Quarterly' THEN DATE(date_trunc('quarter', pp.startdate + INTERVAL '3 MONTH'))
             WHEN pt.name = 'Yearly' THEN DATE(date_trunc('year', pp.startdate + INTERVAL '1 YEAR'))
        END as new_date
        FROM datavalue dv 
        LEFT JOIN period pp on dv.periodid = pp.periodid
        LEFT JOIN periodtype pt on pp.periodtypeid = pt.periodtypeid
        ORDER BY pp.startdate DESC
    )
    UPDATE datavalue dv
    SET periodid = new_period.periodid
    FROM tbl_shift_date
    INNER JOIN period new_period on tbl_shift_date.periodtypeid = new_period.periodtypeid AND new_period.startdate = tbl_shift_date.new_date
    WHERE
        dv.dataelementid = tbl_shift_date.dataelementid AND
        dv.sourceid = tbl_shift_date.sourceid AND
        dv.categoryoptioncomboid = tbl_shift_date.categoryoptioncomboid AND
        dv.attributeoptioncomboid = tbl_shift_date.attributeoptioncomboid AND
        dv.value = tbl_shift_date.value AND -- Not part of the unique key
        dv.periodid = tbl_shift_date.old_periodid AND
        tbl_shift_date.frequency = period_type;

    RETURN TRUE;
END
$$;
