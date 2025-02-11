import aws_cdk as core
import aws_cdk.assertions as assertions
from stack.ynr import YnrStack


def test_template_components():
    app = core.App()
    stack = YnrStack(app, "YnrStack")
    template = assertions.Template.from_stack(stack)

    # We're managing the ECS Cluster in-stack, instead of taking a cluster ID
    # as an input param - so it needs to exist.
    template.resource_count_is('AWS::ECS::Cluster', 1)

    # NAT Gateways cost ~0.05USD/hour. To avoid this cost, we currently locate
    # ECS tasks in a public subnet, and give each task instance a public IP
    # address solely so that it can pull its container image from DockerHub
    # (currently) and ECR Public (in the future).
    # We can't use an ECR interface VPC endpoint as "VPC endpoints currently
    # don't support Amazon ECR Public repositories"
    # cf. https://docs.aws.amazon.com/AmazonECR/latest/userguide/vpc-endpoints.html
    # This cost tradeoff breaks down at 10 ECS task instances per NAT Gateway
    # (i.e. per AWS AZ), as public IP addresses are charged at 0.005USD/hour.
    # For now, we simply ensure that zero NAT Gateways exist in the stack.
    template.resource_count_is('AWS::EC2::NatGateway', 0)
