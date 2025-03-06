from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_kms as kms
from aws_cdk import aws_ssm as ssm
from constructs import Construct


class YnrStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        publicSubnet = ec2.SubnetConfiguration(
            name="Public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24
        )

        vpc = ec2.Vpc(
            self,
            "YnrVpc",
            enable_dns_hostnames=False,
            enable_dns_support=True,
            create_internet_gateway=True,
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[publicSubnet],
        )

        cluster = ecs.Cluster(self, "YnrCluster", vpc=vpc)

        ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "YnrService",
            cluster=cluster,
            assign_public_ip=True,
            cpu=512,
            memory_limit_mib=1024,
            desired_count=2,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry(
                    "amazon/amazon-ecs-sample"
                ),
                # Secrets aren't necessarily "secret", but are created as
                # environment variables that are looked up at ECS task
                # instantiation.
                secrets={
                    "DJANGO_SETTINGS_MODULE": ecs.Secret.from_ssm_parameter(
                        ssm.StringParameter.from_string_parameter_name(
                            self,
                            "DSM",
                            "/dc/ynr/dev/1/web/DJANGO_SETTINGS_MODULE",
                        )
                    )
                },
                environment={
                    "YNR_DJANGO_SECRET_KEY": "insecure",
                },
            ),
            public_load_balancer=True,
        )
