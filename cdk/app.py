#!/usr/bin/env python3

import os

import aws_cdk as cdk
from stack.ynr import YnrStack

app = cdk.App()
YnrStack(
    app,
    "YnrStack",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
)

app.synth()
