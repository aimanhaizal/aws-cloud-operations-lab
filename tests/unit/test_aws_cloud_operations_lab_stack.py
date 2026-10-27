
import aws_cdk as core
import aws_cdk.assertions as assertions

from aws_cloud_operations_lab.aws_cloud_operations_lab_stack import (
    AwsCloudOperationsLabStack,
)


def test_vpc_has_expected_network_configuration():
    app = core.App()
    stack = AwsCloudOperationsLabStack(app, "CloudOpsTestStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::EC2::VPC", 1)
    template.has_resource_properties(
        "AWS::EC2::VPC",
        {
            "CidrBlock": "10.20.0.0/16",
            "EnableDnsSupport": True,
            "EnableDnsHostnames": True,
        },
    )


def test_vpc_has_four_subnets_and_no_nat_gateway():
    app = core.App()
    stack = AwsCloudOperationsLabStack(app, "CloudOpsTestStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::EC2::Subnet", 4)
    template.resource_count_is("AWS::EC2::NatGateway", 0)


def test_public_subnets_have_internet_routes():
    app = core.App()
    stack = AwsCloudOperationsLabStack(app, "CloudOpsTestStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::EC2::InternetGateway", 1)
    template.resource_count_is("AWS::EC2::VPCGatewayAttachment", 1)
    template.resource_count_is("AWS::EC2::Route", 2)


def test_no_ec2_instances_are_created_yet():
    app = core.App()
    stack = AwsCloudOperationsLabStack(app, "CloudOpsTestStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::EC2::Instance", 0)


def test_alb_security_group_allows_http():
    app = core.App()
    stack = AwsCloudOperationsLabStack(app, "CloudOpsTestStack")
    template = assertions.Template.from_stack(stack)

    template.has_resource_properties(
        "AWS::EC2::SecurityGroup",
        {
            "GroupDescription": "Allows public HTTP traffic to the future ALB",
            "SecurityGroupIngress": [
                {
                    "CidrIp": "0.0.0.0/0",
                    "Description": "Allow HTTP from the internet",
                    "FromPort": 80,
                    "IpProtocol": "tcp",
                    "ToPort": 80,
                }
            ],
        },
    )



def test_app_security_group_restricts_ingress_to_alb():
    app = core.App()
    stack = AwsCloudOperationsLabStack(app, "CloudOpsTestStack")
    template = assertions.Template.from_stack(stack)

    resources = template.to_json()["Resources"]

    alb_sg_ids = {
        logical_id
        for logical_id, resource in resources.items()
        if resource["Type"] == "AWS::EC2::SecurityGroup"
        and resource.get("Properties", {}).get("GroupDescription")
        == "Allows public HTTP traffic to the future ALB"
    }

    assert len(alb_sg_ids) == 1
    alb_sg_id = next(iter(alb_sg_ids))

    ingress_rules = [
        resource["Properties"]
        for resource in resources.values()
        if resource["Type"] == "AWS::EC2::SecurityGroupIngress"
    ]

    app_rules = [
        rule
        for rule in ingress_rules
        if rule.get("FromPort") == 8000
        and rule.get("ToPort") == 8000
    ]

    assert len(app_rules) == 1
    assert app_rules[0]["IpProtocol"] == "tcp"
    assert app_rules[0]["SourceSecurityGroupId"] == {
        "Fn::GetAtt": [alb_sg_id, "GroupId"]
    }
    assert "CidrIp" not in app_rules[0]
    assert "CidrIpv6" not in app_rules[0]
