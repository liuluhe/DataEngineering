from aws_cdk import (
    aws_glue as glue,
    aws_iam as iam,
    core
)

class RSGlueJob (core.Stack):

    def __init__(self, scope: core.Construct, id: str, script_path:str, job_name:str
        ,dbname:str,cluster_id:str,host:str,port:int,username:str,password:str
        ,sql_script_bucket:str,sql_script_key:str,dependent_packages_path:str
        ,**kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        policy_statement = iam.PolicyStatement(
                actions=["logs:*","s3:*","ec2:*","iam:*","cloudwatch:*","dynamodb:*","glue:*","redshift:*","redshift-data:*"]
            )

        policy_statement.add_all_resources()

        glue_job_role = iam.Role(
            self,
            "Glue-Job-Role-Demo",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com")
        )
        glue_job_role.add_to_policy(policy_statement)




        job = glue.CfnJob(
            self,
            "glue-redshift-job",
            role=glue_job_role.role_arn,
            max_capacity=0.0625,
            #glue_version = "2.0",
            name = job_name,
            default_arguments = {
                 '--dbname':   dbname,
                 '--host':  host,
                 '--port':  port,
                 '--username': username,
                 '--cluster_id':cluster_id,
                 '--password': password,
                 '--sql_script_bucket': sql_script_bucket,
                 '--sql_script_key':sql_script_key,
                 '--extra-py-files':dependent_packages_path},
            command=glue.CfnJob.JobCommandProperty(
                name="pythonshell",
                script_location=script_path,
                python_version = "3"
            )
        )
