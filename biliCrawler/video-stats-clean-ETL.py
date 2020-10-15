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
## @type: DataSource
## @args: [database = "livecodingdemo", table_name = "raw_video_stats", transformation_ctx = "datasource0"]
## @return: datasource0
## @inputs: []
datasource0 = glueContext.create_dynamic_frame.from_catalog(database = "livecodingdemo", table_name = "raw_video_stats", transformation_ctx = "datasource0")
resolvechoice2 = datasource0.resolveChoice(specs = [('mid','cast:string')])

if datasource0.count()!=0:
    glueContext.write_dynamic_frame.from_options(frame = resolvechoice2, connection_type = "s3", connection_options = {"path": "s3://aws-demo-live-code-demo/data/video-stats-clean/","partitionKeys": ["mid","year"]}, format = "parquet", transformation_ctx = "datasink0")

job.commit()