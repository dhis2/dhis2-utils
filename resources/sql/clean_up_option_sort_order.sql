/**
    This tool is used for cleaning up gaps in OptionSet.options.sortOrder
    An example of corrupted sort_orders can be [2,5,7] and after cleaning up, the correct sort_order list should be [1,2,3]
    Before cleaning up, please check your database using below validation query to check if there are any corrupted sort_orders.
**/

--Execute this query to detect options that have corrupted sort_order.
select ov.sort_order, ov.optionvalueid, ov.optionsetid 
from optionvalue ov, 
    ( select optionsetid, optionvalueid, row_number() over ( partition by optionsetid order by sort_order ) as orderIndex from optionvalue  ) as temp 
where ov.sort_order <> temp.orderIndex and ov.optionsetid = temp.optionsetid and ov.optionvalueid = temp.optionvalueid 
order by ov.optionsetid, ov.optionvalueid;
/**
Example:
sort_order | optionvalueid | optionsetid
------------+---------------+-------------
          2 |       1202979 |     1203014
          3 |       1202980 |     1203014
          4 |       1202977 |     1203014
          8 |       1202978 |     1203014
          8 |       1202981 |     1203015
          9 |       1202982 |     1203015
         10 |       1202983 |     1203015
         11 |       1202984 |     1203015
         12 |       1202985 |     1203016
         13 |       1202986 |     1203016
**/


-- After getting the result from above query, you can use this query to select all sort_order of an optionset and check again for the gaps
select sort_order, optionvalueid from optionvalue where optionsetid = 1203014 order by sort_order;
/**
Example: this sort_order list should be [1,2,3,4]
  sort_order | optionvalueid
------------+---------------
          2 |       1202979
          3 |       1202980
          4 |       1202977
          8 |       1202978
(4 rows)

/**
    Clean up query for all records in optionvalue table. Only execute this after validation using above query and backup your data.
    This query is idempotent.
**/
update optionvalue 
set sort_order = temp.orderIndex
from 
( select optionvalueid, optionsetid, row_number() 
	over ( partition by optionsetid order by sort_order ) as orderIndex
	from optionvalue ) temp
where temp.optionvalueid = optionvalue.optionvalueid and temp.optionsetid = optionvalue.optionsetid;

/**
Check after cleaning up

dev=# select sort_order, optionvalueid from optionvalue where optionsetid = 1203014 order by sort_order;
sort_order | optionvalueid
------------+---------------
          1 |       1202979
          2 |       1202980
          3 |       1202977
          4 |       1202978
(4 rows)
**/