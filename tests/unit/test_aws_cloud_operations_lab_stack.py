
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


def test_vpc_has_two_public_and_two_isolated_subnets():
    app = core.App()
    stack = AwsCloudOperationsLabStack(app, "CloudOpsTestStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::EC2::Subnet", 4)
    template.resource_count_is(
        "AWS::EC2::NatGateway",
        0,
    )

    template.has_resource_properties(
        "AWS::EC2::Subnet",
        {
            "CidrBlock": "10.20.0.0/24",
            "MapPublicIpOnLaunch": True,
        },
    )


def test_public_subnets_have_internet_routes():
    app = core.App()
    stack = AwsCloudOperationsLabStack(app, "CloudOpsTestStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::EC2::InternetGateway", 1)
    template.resource_count_is("AWS::EC2::VPCGatewayAttachment", 1)

    template.resource_count_is(
        "AWS::EC2::Route",
        2,
    )


def test_no_nat_gateway_or_nat_instance_is_defined():
    app = core.App()
    stack = AwsCloudOperationsLabStack(app, "CloudOpsTestStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::EC2::NatGateway", 0)
    template.resource_count_is("AWS::EC2::Instance", 0)
