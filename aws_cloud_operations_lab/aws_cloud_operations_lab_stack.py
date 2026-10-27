
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
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
