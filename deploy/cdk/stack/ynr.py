from aws_cdk import Stack
from aws_cdk import aws_s3 as s3
from constructs import Construct


class YnrStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = s3.Bucket(self, 'test')  # noqa: F841
