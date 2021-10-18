from aws_cdk import aws_redshift as redshift
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_secretsmanager as sm
from aws_cdk import core



class RedshiftStack(core.Stack):

    def __init__(
        self,
        scope: core.Construct, id: str,
        vpc,
        ec2_instance_type: str,
        master_user: str,
        password:str,
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        _rs_cluster_role = iam.Role(
            self, "redshiftClusterRole",
            assumed_by=iam.ServicePrincipal(
                "redshift.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonS3ReadOnlyAccess"
                )
            ]
        )

        # Subnet Group for Cluster
        demo_cluster_subnet_group = redshift.CfnClusterSubnetGroup(
            self,
            "redshiftDemoClusterSubnetGroup",
            subnet_ids=vpc.get_vpc_public_subnet_ids,
            description="Redshift Demo Cluster Subnet Group"
        )

        # create redshift security group
        self.redshift_sg = ec2.SecurityGroup( self,
            id="redshiftSecurityGroup",
            vpc=vpc.get_vpc,
            security_group_name=f"redshift_sg",
            description="Security Group for Redshift")
        self.redshift_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(5439), 'Public login access')



        self.demo_cluster = redshift.CfnCluster(
            self,
            "redshiftDemoCluster",
            cluster_type="single-node",
            cluster_identifier = "redshift-stack",
            db_name="dev",
            master_username=master_user,
            port=5439,
            publicly_accessible=True,
            master_user_password=password,
            iam_roles=[_rs_cluster_role.role_arn],
            node_type=f"{ec2_instance_type}",
            cluster_subnet_group_name=demo_cluster_subnet_group.ref,
            vpc_security_group_ids=[self.redshift_sg.security_group_id]
        )

        ###########################################
        ################# OUTPUTS #################
        ###########################################
        output_1 = core.CfnOutput(
            self,
            "RedshiftCluster",
            value=f"{self.demo_cluster.attr_endpoint_address}",
            description=f"RedshiftCluster Endpoint"
        )
        output_2 = core.CfnOutput(
            self,
            "RedshiftClusterId",
            value=(
                f"{self.demo_cluster.cluster_identifier}"
        ),
            description=f"Redshift Cluster id"
        )
        output_3 = core.CfnOutput(
            self,
            "RedshiftIAMRole",
            value=(
                f"{_rs_cluster_role.role_arn}"
            ),
            description=f"Redshift Cluster IAM Role Arn"
        )

    @property
    def get_security_group(self):
        return self.redshift_sg
    @property
    def get_cluster(self):
        return self.demo_cluster
    