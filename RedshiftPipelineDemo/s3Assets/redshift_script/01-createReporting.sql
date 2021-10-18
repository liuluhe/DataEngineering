create table if not exists test.quarter_revenue_report(
  quarter char(10),
  warehouse_num int,
  revenue decimal, 
  item_quantity bigint
)
diststyle even
sortkey(quarter,warehouse_num)
;