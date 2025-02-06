import aws_cdk as core
import aws_cdk.assertions as assertions
from stack.ynr import YnrStack


def test_one_s3_bucket():
    app = core.App()
    stack = YnrStack(app, "YnrStack")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is('AWS::S3::Bucket', 1)
