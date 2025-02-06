#!/usr/bin/env python3

import aws_cdk as cdk
from stack.ynr import YnrStack

app = cdk.App()
YnrStack(app, "YnrStack",
    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.
    #env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
    )

app.synth()
