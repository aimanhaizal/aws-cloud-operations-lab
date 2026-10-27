
#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cloud_operations_lab.aws_cloud_operations_lab_stack import (
    AwsCloudOperationsLabStack,
)

app = cdk.App()

AwsCloudOperationsLabStack(
    app,
    "AwsCloudOperationsLabStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=os.getenv("CDK_DEFAULT_REGION", "ap-southeast-1"),
    ),
)

app.synth()
