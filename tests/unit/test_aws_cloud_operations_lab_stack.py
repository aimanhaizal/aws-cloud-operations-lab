import aws_cdk as core
import aws_cdk.assertions as assertions

from aws_cloud_operations_lab.aws_cloud_operations_lab_stack import AwsCloudOperationsLabStack

# example tests. To run these tests, uncomment this file along with the example
# resource in aws_cloud_operations_lab/aws_cloud_operations_lab_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AwsCloudOperationsLabStack(app, "aws-cloud-operations-lab")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
