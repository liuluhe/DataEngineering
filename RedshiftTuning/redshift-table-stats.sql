
/**********************************************************************************************
Purpose: Return Table level storage information (size, skew, etc)
Columns:
	table_id:     	Table id
	schema:       	Schema name
	table:        	Table name
	mbytes:       	Size of the table in Megabytes
	tbl_rows:     	Number of rows
	diststyle:    	Distribution Key (shows EVEN for event disttributed, ALL for Diststyle ALL)
	encoded:      	Y if the table has at least one compressed column, N otherwise
	pct_enc:      	Proportion of number of encoded columns to total number of columns
	skew_rows:    	Table Skew. Proportion between largest slice and smallest slice (null for diststyle ALL)
	sortkey_num:  	Number of columns in the compound sortkey
	sortkey1:     	First column of Sortkey
	skew_sortkey1:	Ratio of the size of the largest non-sort key column to the size of the first column of the sort key, if a sort key is defined. Use this value to evaluate the effectiveness of the sort key. 
	sortkey1_enc:   Compression encoding of the first column in the sort key, if a sort key is defined
	stats_off:		Measure of staleness of table statistics (real size versus size recorded in stats)
	unsorted:		Proportion of unsorted rows compared to total rows
	max_varchar:	Size of the largest column that uses a VARCHAR data type
	pct_of_total: 	Size of the table in proportion to the cluster size
Author: liuluhe
Created At: 2021-09-24
**********************************************************************************************/

with a as
(SELECT table_id,"schema","table",size as mbytes,tbl_rows,diststyle,encoded,skew_rows,sortkey_num,sortkey1,skew_sortkey1,sortkey1_enc,stats_off,unsorted,max_varchar
FROM svv_table_info
WHERE schema not in ('pg_internal')
ORDER BY size DESC) 
,b as
(SELECT attrelid,SUM(case when attencodingtype <> 0 then 1 else 0 end)::DECIMAL(20,3)/COUNT(attencodingtype)::DECIMAL(20,3)  *100.00 as pct_enc
FROM pg_attribute
GROUP BY 1)
select table_id,"schema","table", mbytes,tbl_rows,diststyle,encoded,pct_enc,skew_rows,sortkey_num,sortkey1,skew_sortkey1,sortkey1_enc,stats_off,unsorted,max_varchar
from a join b on a.table_id=b.attrelid;