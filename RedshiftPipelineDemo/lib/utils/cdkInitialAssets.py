from aws_cdk import (
    aws_glue as glue,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    core
)

import os

class S3Assets (core.Stack):

    def __init__(self, scope: core.Construct, id: str, local_directory:str,**kwargs) -> None:
        super().__init__(scope, id, **kwargs)
    

        self.s3bucket = s3.Bucket(self, 'S3demo')
        s3deploy.BucketDeployment(self, 's3deploy', sources =[s3deploy.Source.asset(os.getcwd()+ "/"+local_directory)]
            ,destination_bucket=self.s3bucket)


        #core.CfnOutput(self, "S3BucketName", value=self.s3bucket.bucket_name,export_name="s3_script_path")
    @property
    def get_bucket(self):
        return self.s3bucket.bucket_name