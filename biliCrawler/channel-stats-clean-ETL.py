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

df_owner = spark.read.json('s3://aws-demo-live-code-demo/data/owner-stats/')

import time
from datetime import datetime,timedelta

y = time.localtime().tm_year
m = time.localtime().tm_mon
d = time.localtime().tm_mday -1
df_delta = df_owner.filter((df_owner.year==y)&(df_owner.month==m)&(df_owner.day==d))
df_owner_final = df_delta.select('crawl_date','follower','following','mid','video_counts').distinct()
df_owner_final.write.format('parquet').mode("append").partitionBy('mid').save("s3://aws-demo-live-code-demo/data/owner-stats-clean/") 

job.commit()