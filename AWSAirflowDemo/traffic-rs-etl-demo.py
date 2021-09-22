from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.utils.dates import days_ago

# [START howto_operator_s3_to_redshift_env_variables]
S3_BUCKET = "test-liuluhe-tokyo"
S3_KEY = "athenademo/traffic-collision-one-file/"
REDSHIFT_TABLE = "traffic_collision_events_airflow"
# [END howto_operator_s3_to_redshift_env_variables]


with DAG(
    dag_id="traffic_agg_etl", start_date=days_ago(1), schedule_interval=None, tags=['example']
) as dag:
    setup__task_create_table = PostgresOperator(
        sql=f'CREATE TABLE IF NOT EXISTS {REDSHIFT_TABLE}(like  traffic_collision_events)',
        postgres_conn_id='redshift',
        task_id='setup__create_table',
    )
    task_transfer_s3_to_redshift = S3ToRedshiftOperator(
        s3_bucket=S3_BUCKET,
        s3_key=S3_KEY,
        schema="PUBLIC",
        table=REDSHIFT_TABLE,
        redshift_conn_id='redshift',
        copy_options=["delimiter as ','","IGNOREHEADER 1","REMOVEQUOTES"],
        task_id='transfer__s3_to_redshift',
    )
    teardown__task_drop_tables = PostgresOperator(
        sql=f'DROP TABLE IF EXISTS agg_traffic_count;\nDROP TABLE IF EXISTS {REDSHIFT_TABLE};',
        postgres_conn_id='redshift',
        task_id='teardown__drop_tables',
    )
    task_create_agg_table = PostgresOperator(
        sql=f'CREATE TABLE agg_traffic_count as select area_name, count(*) from {REDSHIFT_TABLE} group by area_name',
        postgres_conn_id='redshift',
        task_id='transfer__create_agg_table',
    )
    [setup__task_create_table, teardown__task_drop_tables]>> task_transfer_s3_to_redshift >> task_create_agg_table
