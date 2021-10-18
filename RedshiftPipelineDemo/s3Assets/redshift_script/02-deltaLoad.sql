insert into test.quarter_revenue_report
select d_quarter_name, cs_warehouse_sk,sum(cs_sales_price*cs_quantity) as revenue, sum(cs_quantity) as item_count
from catalog_sales a join date_dim b on a.cs_sold_date_sk=b.d_date_sk 
where d_quarter_name > '2000Q1'
group by d_quarter_name,cs_warehouse_sk