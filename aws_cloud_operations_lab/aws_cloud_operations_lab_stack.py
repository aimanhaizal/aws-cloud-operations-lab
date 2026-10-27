
import aws_cdk as cdk

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct



class AwsCloudOperationsLabStack(Stack):
    """Network foundation for the Cloud Operations Lab."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(
            self,
            "CloudOpsVpc",
            vpc_name="cloud-operations-lab-vpc",
            ip_addresses=ec2.IpAddresses.cidr("10.20.0.0/16"),
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )

        self.alb_security_group = ec2.SecurityGroup(
            self,
            "AlbSecurityGroup",
            vpc=self.vpc,
            description="Allows public HTTP traffic to the future ALB",
            allow_all_outbound=True,
        )

        self.alb_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "Allow HTTP from the internet",
        )

        self.app_security_group = ec2.SecurityGroup(
            self,
            "AppSecurityGroup",
            vpc=self.vpc,
            description="Allows application traffic only from the ALB",
            allow_all_outbound=True,
        )

        self.app_security_group.add_ingress_rule(
            self.alb_security_group,
            ec2.Port.tcp(8000),
            "Allow application traffic from the ALB",
        )


        # IAM role for secure Systems Manager administration.
        instance_role = iam.Role(
            self,
            "CloudOpsInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "CloudWatchAgentServerPolicy"
                ),
            ],
        )

        # First EC2 host: no inbound SSH or direct public app access.
        self.app_instance = ec2.Instance(
            self,
            "CloudOpsAppInstance",
            instance_type=ec2.InstanceType("t3.micro"),
            machine_image=ec2.MachineImage.generic_linux(
                {"ap-southeast-1": "ami-058799d8c91389327"}
            ),
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC,
            ),
            security_group=self.app_security_group,
            role=instance_role,
            associate_public_ip_address=True,
            require_imdsv2=True,
            user_data_causes_replacement=True,
        )

        # Install Docker. Application deployment comes next.
        self.app_instance.add_user_data(
            "set -eux",
            "dnf update -y",
            "dnf install -y docker",
            "systemctl enable --now docker",
            "usermod -aG docker ec2-user",
        )

        cdk.CfnOutput(
            self,
            "CloudOpsInstanceId",
            value=self.app_instance.instance_id,
            description="EC2 instance ID for the CloudOps application",
        )
