create table test.store_return_stats as
select d_moy,d_year, sr_store_sk,count(distinct sr_customer_sk)as cust_cnt, sum(sr_net_loss) as net_loss
from store_returns a join date_dim b on a.sr_returned_date_sk=b.d_date_sk 
group by d_moy,d_year, sr_store_sk;