/**
    This function is used for reordering the table "visualization_organisationunits".
    It ensures that the "sort_order" column starts from 0 for each "visualizationid".
    The existing order within each "visualizationid" is maintained.

    Usage:
        1) Execute below query to create the function reorder_visualization_organisationunits().
        2) Call the function by executing "SELECT reorder_visualization_organisationunits()".
**/
CREATE OR REPLACE FUNCTION reorder_visualization_organisationunits()
RETURNS text
AS $$
DECLARE
    row_count integer;
BEGIN
    -- Update the sort_order to be sequential starting from 0 for each visualizationid
    UPDATE visualization_organisationunits
    SET sort_order = sub.new_sort_order
    FROM (
        SELECT
            visualizationid,
            organisationunitid,
            ROW_NUMBER() OVER (PARTITION BY visualizationid ORDER BY sort_order) - 1 AS new_sort_order
        FROM
            visualization_organisationunits
    ) AS sub
    WHERE
        visualization_organisationunits.visualizationid = sub.visualizationid
        AND visualization_organisationunits.organisationunitid = sub.organisationunitid
        AND visualization_organisationunits.sort_order <> sub.new_sort_order;

    GET DIAGNOSTICS row_count = ROW_COUNT;
    RETURN 'Reordered ' || row_count || ' records in visualization_organisationunits.';
END;
$$ LANGUAGE plpgsql;