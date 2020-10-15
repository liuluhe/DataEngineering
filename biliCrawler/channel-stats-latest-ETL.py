import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

## @params: [JOB_NAME]
args = getResolvedOptions(sys.argv, ['JOB_NAME'])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

datasource0 = glueContext.create_dynamic_frame.from_catalog(database = "livecodingdemo", table_name = "raw_video_stats", transformation_ctx = "datasource0")
df_owner = spark.read.json('s3://aws-demo-live-code-demo/data/owner-stats/')
df_video = datasource0.toDF()

from pyspark.sql.functions import *
from pyspark.sql.window import Window

rank_owner =  df_owner.withColumn("rank", row_number().over(Window.partitionBy("mid").orderBy(desc("crawl_date"))))
filter_owner = rank_owner.filter(rank_owner.rank == 1)

from pyspark.sql.functions import explode
df_flat = filter_owner.select('mid', 'follower','video_counts','crawl_date', explode('tag').alias('flat'))
df = df_flat.select('mid', 'follower','video_counts','crawl_date', df_flat['flat'].getItem("游戏").alias('tag:game'),df_flat['flat'].getItem("生活").alias('tag:life'),df_flat['flat'].getItem("知识").alias('tag:knowledge'),df_flat['flat'].getItem("美食").alias('tag:food'),df_flat['flat'].getItem("音乐").alias('tag:music'),df_flat['flat'].getItem("纪录片").alias('tag:documentary'))
df_final = df.groupBy('mid', 'follower','video_counts','crawl_date').agg(max('tag:game').alias('tag:game'),max('tag:life').alias('tag:life'),max('tag:knowledge').alias('tag:knowledge'),max('tag:documentary').alias('tag:documentary'),max('tag:food').alias('tag:food'),max('tag:music').alias('tag:mucis'))


df_final.write.format('parquet').mode("overwrite").save("s3://aws-demo-live-code-demo/data/owner-stats-latest/") 
job.commit()