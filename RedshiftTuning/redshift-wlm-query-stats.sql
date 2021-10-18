/**********************************************************************************************
Purpose: Returns the per-hour WLM queue statitics. These results can be used 
    to fine tune WLM queues which contain too many or too few slots, resulting in WLM queuing 
    or unutilized cluster memory. With hourly aggregates you can leverage dynamic WLM changes
    to ensure your cluster is correctly configured for workloads with a predictable pattern.
    
Columns:	
	exec_hour:				1 hour UTC range of time. 
	service_class: 			ID for the service class, defined in the WLM configuration file. 
	num_query:				Number of queries executed on that queue/hour
	num_evict:				Number of queries
	avg_q_sec:				Average Queueing time in seconds
	avg_e_sec:				Averagte Executiong time in seconds	
	avg_pct_cpu:      		Average percentage of CPU used by the query. Value can be more than 100% for multi-cpu/slice systems
    max_pct_cpu:      		Max percentage of CPU used by the query. Value can be more than 100% for multi-cpu/slice systems
    sum_spill_mb:     		Sum of Spill usage by that queue on that hour
    sum_row_scan:     		Sum of rows scanned on that queue/hour
    sum_join_rows:   		Sum of rows joined on that queue/hour
    sum_nl_join_rows: 		Sum of rows Joined using Nested Loops on that queue/hour
    sum_ret_rows:     		Sum of rows returned to the leader/client on that queue/hour
    sum_spec_mb:      		Sum of Megabytes scanned by a Spectrum query on that queue/hour
    max_wlm_concurrency: 	Current actual concurrency level of the service class.
    max_service_class_slots:Max number of WLM query slots in the service_class at a point in time.
Author: liuluhe
Created At: 2021-09-24
**********************************************************************************************/

WITH generate_dt_series AS 
(select sysdate - (n * interval '1 second') as dt from (select row_number() over () as n from stl_scan limit 604800))
,apex AS 
(SELECT iq.dt, iq.service_class, iq.num_query_tasks, count(iq.slot_count) as service_class_queries, sum(iq.slot_count) as service_class_slots
 FROM (select gds.dt, wq.service_class, wscc.num_query_tasks, wq.slot_count
                FROM stl_wlm_query wq
                JOIN stv_wlm_service_class_config wscc ON (wscc.service_class = wq.service_class AND wscc.service_class > 4)
                JOIN generate_dt_series gds ON (wq.service_class_start_time <= gds.dt AND wq.service_class_end_time > gds.dt)
                WHERE wq.userid > 1 AND wq.service_class > 4) iq
        GROUP BY iq.dt, iq.service_class, iq.num_query_tasks)
,maxes as (SELECT apex.service_class, date_trunc('hour',apex.dt) as exec_hour, max(service_class_slots) max_service_class_slots
                        from apex group by apex.service_class, date_trunc('hour',apex.dt))
, wlm_hourly as(
    SELECT maxes.exec_hour,apex.service_class, apex.num_query_tasks as max_wlm_concurrency, MAX(apex.service_class_slots) as max_service_class_slots
FROM apex
JOIN maxes ON (apex.service_class = maxes.service_class AND apex.service_class_slots = maxes.max_service_class_slots)
GROUP BY  apex.service_class, apex.num_query_tasks, maxes.exec_hour
ORDER BY apex.service_class, maxes.exec_hour
)
, hourly_usage as (
    select date_trunc('hour', convert_timezone('utc','utc',w.exec_start_time)) as exec_hour, w.service_class, sum(decode(w.final_state, 'Completed',1,'Evicted',0,0)) as num_query,  sum(decode(w.final_state, 'Completed',0,'Evicted',1,0)) as n_ev, avg(w.total_queue_time/1000000) as avg_q_sec, avg(w.total_exec_time/1000000) as avg_e_sec,
       avg(m.query_cpu_usage_percent) as avg_pct_cpu, max(m.query_cpu_usage_percent) as max_pct_cpu, max(m.query_temp_blocks_to_disk) as max_spill, sum(m.query_temp_blocks_to_disk) as sum_spill_mb, sum(m.scan_row_count) as sum_row_scan, sum(m.join_row_count) as sum_join_rows, sum(m.nested_loop_join_row_count) as sum_nl_join_rows, 
       sum(m.return_row_count) as sum_ret_rows, sum(m.spectrum_scan_size_mb) as sum_spec_mb
from   stl_wlm_query as w left join svl_query_metrics_summary as m using (userid,service_Class, query)
where  service_class > 5 
  and     w.exec_start_time >=  dateadd(day, -1, current_Date) group by 1,2 
union all
select date_trunc('hour', convert_timezone('utc','utc',c.starttime)) as exec_hour, 0 as "service_class", sum(decode(c.aborted, 1,0,1)) as num_query,  sum(decode(c.aborted, 1,1,0)) as n_ev, 0 as avg_q_sec, avg(c.elapsed/1000000) as avg_e_sec,
       0 as avg_pct_cpu, 0 as max_pct_cpu, 0 as max_spill, 0 as sum_spill_mb, 0 as sum_row_scan, 0 as sum_join_rows, 0 as sum_nl_join_rows, sum(m.return_row_count) as sum_ret_rows, 0 as sum_spec_mb
from svl_qlog c left join svl_query_metrics_summary as m on ( c.userid = m.userid and c.source_query=m.query ) 
 where source_query is not null and     c.starttime >=  dateadd(day, -1, current_Date)
group by 1,2  order by  1 desc,2
)    
select a.exec_hour,a.service_class,num_query,n_ev,avg_q_sec,avg_e_sec,avg_pct_cpu,max_pct_cpu,max_spill,sum_spill_mb,sum_row_scan,sum_join_rows,sum_nl_join_rows,sum_ret_rows,sum_spec_mb,max_wlm_concurrency,max_service_class_slots
from hourly_usage a left join wlm_hourly b on a.exec_hour=b.exec_hour and a.service_class=b.service_class;



