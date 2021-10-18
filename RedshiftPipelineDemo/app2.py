from aws_cdk import (
    aws_ec2 as ec2,
    core,
)
from cdk.cdkVPCStack import VPCStack
from cdk.cdkRedshiftStack import RedshiftStack
from cdk.cdkGlueStack import RSGlueJob,GlueCheckCondition
from cdk.cdkInitialAssets import S3Assets



app = core.App()

asset = S3Assets(app, "s3-assets",local_directory="s3Assets")
vpc_stack = VPCStack(app,"vpc-stack")
redshift_stack = RedshiftStack(app,"Redshift-stack",vpc_stack,ec2_instance_type="dc2.large",master_user="admin", password="Adim1234")


glue_job = RSGlueJob(app,"Glue-redshift-job",script_path="s3://"+asset.get_bucket+"/glue_script/gluejob_redshiftSQL.py", job_name="Redshift-copy"
                    ,dbname=redshift_stack.get_cluster.db_name
                    ,cluster_id=redshift_stack.get_cluster.cluster_identifier
                    #,host=redshift_stack.get_cluster.attr_endpoint_address
                    #,port=redshift_stack.get_cluster.attr_endpoint_port
                    ,username=redshift_stack.get_cluster.master_username
                    #,password=redshift_stack.get_cluster.master_user_password
                    ,sql_script_bucket=asset.get_bucket
                    ,sql_script_key="redshift_script/test.sql"
                    ,dependent_packages_path="s3://"+asset.get_bucket+"/boto3-depends.zip")


   
app.synth()