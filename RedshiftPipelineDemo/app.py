#!/usr/bin/env python3
#import os

from aws_cdk import (
    aws_ec2 as ec2,
    core,
)
from lib.utils.cdkVPCStack import VPCStack
from lib.utils.cdkRedshiftStack import RedshiftStack
from lib.utils.cdkGlueStack import RSGlueJob,GlueCheckCondition
from lib.utils.cdkInitialAssets import S3Assets
from lib.pipelines.catalogSalesReporting import CatalogSalesReporting



app = core.App()

asset = S3Assets(app, "s3-assets",local_directory="s3Assets")

# Need your input for the redshift configuration
workflow = CatalogSalesReporting (app,"Redshift-reporting-pipeline"
        ,dbname="dev"
        ,username="awsuser"
        ,password="*****"
        ,host="redshift-benchmark.********.cn-northwest-1.redshift.amazonaws.com.cn"
        ,port=5179
        ,cluster_id="redshift-benchmark"
        ,s3_bucket=asset.get_bucket)


app.synth()
