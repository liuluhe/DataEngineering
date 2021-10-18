from aws_cdk import (
    aws_glue as glue,
    aws_iam as iam,
    core
)


class CatalogSalesReporting (core.Stack):
    def __init__(self, scope: core.Construct, id: str
        ,dbname:str
        ,password:str
        ,username:str
        ,host:str
        ,port:int
        ,cluster_id:str
        ,s3_bucket:str
        ,**kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # create role for Glue jobs, in prod this could be a bring in value or create by initiation
        policy_statement = iam.PolicyStatement(
                actions=["logs:*","s3:*","ec2:*","iam:*","cloudwatch:*","dynamodb:*","glue:*","redshift:*","redshift-data:*"]
            )

        policy_statement.add_all_resources()

        self.glue_job_role = iam.Role(
            self,
            "Glue-Job-Role-Demo",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com")
        )
        self.glue_job_role.add_to_policy(policy_statement)

        self.dbname=dbname
        self.username=username
        self.cluster_id=cluster_id
        self.s3_bucket=s3_bucket
        self.password=password
        self.host=host
        self.port=port
        
        ############################### Create Glue jobs#############################################
        ddl_task = self.rs_sql_task("redshift-create-reporting-table", "01-createReporting.sql")
        deltaload_task = self.rs_sql_task("redshift-deltaload-reporting","02-deltaLoad.sql")
        fullload_return_task = self.rs_sql_task("redshift-fullload-return","02-fullLoadReturn.sql")
        cleanup_task = self.rs_sql_task("redshift-cleanup","03-cleanUp.sql")
        check_task = glue.CfnJob(
            self,
            "time-checker",
            role=self.glue_job_role.role_arn,
            max_capacity=0.0625,
            name = "time-checker",
            tags={"project":"redshift-demo"},
            command=glue.CfnJob.JobCommandProperty(
                name="pythonshell",
                script_location="s3://"+self.s3_bucket+"/glue_script/time_check.py",
                python_version = "3"
            )
        )

        ################################## Create workflow #########################################
        quarterly_reporting=glue.CfnWorkflow(self, "quarterly-catalog-reporting-pipeline"
            , description="Quarterly report pipeline for catalog sales"
            , name="quarterly-catalog-reporting"
            , tags={"project":"redshift-demo"})
        
        ############### Define pipeline dag by creating trigger and add to workflow#################
        start=glue.CfnTrigger(self, "start-trigger"
            , actions=[glue.CfnTrigger.ActionProperty(job_name=ddl_task.name),glue.CfnTrigger.ActionProperty(job_name=fullload_return_task.name)] 
            , type="ON_DEMAND" # should be scheduled 
            , description="Start the workflow, will be quarterly scheduled"
            , name="start-redshift-demo"
            , tags={"project":"redshift-demo"}
            #, schedule=cron(15 12 * * ? *)
            , workflow_name=quarterly_reporting.name)

        delta_load=glue.CfnTrigger(self, "delta-trigger"
            , actions=[glue.CfnTrigger.ActionProperty(job_name=deltaload_task.name)]
            , type="CONDITIONAL"
            , description="Based on create DDL completion start incremental data load"
            , name="delta-load-trigger"
            , predicate= 
            {
                "conditions": [
                {
                    "logicalOperator": "EQUALS",
                    "jobName": ddl_task.name,
                    "state": "SUCCEEDED",
                },{
                    "logicalOperator": "EQUALS",
                    "jobName": check_task.name,
                    "state": "SUCCEEDED",
                }
                ],
                "logical": "AND",
            }
            , tags={"project":"redshift-demo"}
            , workflow_name=quarterly_reporting.name)
        time_check = glue.CfnTrigger(self, "time-trigger"
            , actions=[glue.CfnTrigger.ActionProperty(job_name=deltaload_task.name)]
            , type="CONDITIONAL"
            , description="Based on time checker start incremental data load"
            , name="time-trigger"
            , predicate= 
            {
                "conditions": [
                {
                    "logicalOperator": "EQUALS",
                    "jobName": fullload_return_task.name,
                    "state": "SUCCEEDED",
                }
                ],
                "logical": "ANY",
            }
            , tags={"project":"redshift-demo"}
            , workflow_name=quarterly_reporting.name)


        cleanup=glue.CfnTrigger(self, "cleanup"
            , actions=[glue.CfnTrigger.ActionProperty(job_name=cleanup_task.name)]
            , type="CONDITIONAL"
            , description="Clean up the return table"
            , name="clean-trigger"
            , predicate= 
            {
                "conditions": [
                {
                    "logicalOperator": "EQUALS",
                    "jobName": deltaload_task.name,
                    "state": "SUCCEEDED",
                }
                ],
                "logical": "ANY",
            }
            , tags={"project":"redshift-demo"}
            , workflow_name=quarterly_reporting.name)

        # Add dependency check, resources are created symontinously
        start.add_depends_on(ddl_task)
        start.add_depends_on(fullload_return_task)
        delta_load.add_depends_on(deltaload_task)
        delta_load.add_depends_on(check_task)
        time_check.add_depends_on(check_task)
        time_check.add_depends_on(deltaload_task)
        cleanup.add_depends_on(cleanup_task)
        cleanup.add_depends_on(deltaload_task)

      



    def rs_sql_task(self,job_name, sql_file):
        return glue.CfnJob(
            self,
            job_name,
            role=self.glue_job_role.role_arn,
            max_capacity=0.0625,
            name = job_name,
            default_arguments = {
                 '--dbname':   self.dbname,
                 '--username': self.username,
                 '--password': self.password,
                 '--host': self.host,
                 '--port': self.port,
                 '--cluster_id':self.cluster_id,
                 '--sql_script_bucket': self.s3_bucket,
                 '--sql_script_key':'redshift_script/'+sql_file, # Only difference for Redshift SQL task
                 '--extra-py-files':"s3://"+self.s3_bucket+"/boto3-depends.zip"},
            tags={"project":"redshift-demo"},
            command=glue.CfnJob.JobCommandProperty(
                name="pythonshell",
                script_location="s3://"+self.s3_bucket+"/glue_script/gluejob_redshiftSQL.py",
                python_version = "3"
            )
        )
