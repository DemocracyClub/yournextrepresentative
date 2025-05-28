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


        vpc = ec2.Vpc.from_lookup(self, "YnrVpc",
            vpc_id = ssm.StringParameter.value_from_lookup(self, "/dc/ynr/dev/1/vpcid")
        )

        cluster = ecs.Cluster(self, "YnrCluster", vpc=vpc)
        encryption_key = kms.Alias.from_alias_name(self, "SSMKey", "alias/aws/ssm")

        ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "YnrService",
            cluster=cluster,
            assign_public_ip=True,
            cpu=512,
            memory_limit_mib=1024,
            desired_count=2,
            enable_execute_command=True,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry(
                    "public.ecr.aws/h3q9h5r7/dc-test/ynr:v3"
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
                    ),
                    "YNR_AWS_S3_MEDIA_BUCKET": ecs.Secret.from_ssm_parameter(
                        ssm.StringParameter.from_string_parameter_name(
                            self,
                            "MediaBucketName",
                            "/dc/ynr/dev/1/YNR_AWS_S3_MEDIA_BUCKET",
                        )
                    ),
                    "YNR_AWS_S3_MEDIA_REGION": ecs.Secret.from_ssm_parameter(
                        ssm.StringParameter.from_string_parameter_name(
                            self,
                            "MediaBucketRegion",
                            "/dc/ynr/dev/1/YNR_AWS_S3_MEDIA_REGION",
                        )
                    ),
                    "YNR_AWS_S3_SOPN_BUCKET": ecs.Secret.from_ssm_parameter(
                        ssm.StringParameter.from_string_parameter_name(
                            self,
                            "SopnBucketName",
                            "/dc/ynr/dev/1/YNR_AWS_S3_SOPN_BUCKET",
                        )
                    ),
                    "YNR_AWS_S3_SOPN_REGION": ecs.Secret.from_ssm_parameter(
                        ssm.StringParameter.from_string_parameter_name(
                            self,
                            "SopnBucketRegion",
                            "/dc/ynr/dev/1/YNR_AWS_S3_SOPN_REGION",
                        )
                    ),
                    "POSTGRES_USERNAME": ecs.Secret.from_ssm_parameter(
                        ssm.StringParameter.from_secure_string_parameter_attributes(
                            self,
                            "DBUSER",
                            encryption_key=encryption_key,
                            parameter_name="/dc/ynr/dev/1/postgres_username",
                        )
                    ),
                    "POSTGRES_PASSWORD": ecs.Secret.from_ssm_parameter(
                        ssm.StringParameter.from_secure_string_parameter_attributes(
                            self,
                            "DBPASSWD",
                            encryption_key=encryption_key,
                            parameter_name="/dc/ynr/dev/1/postgres_password",
                        )
                    ),
                    "POSTGRES_HOST": ecs.Secret.from_ssm_parameter(
                        ssm.StringParameter.from_secure_string_parameter_attributes(
                            self,
                            "DBHOST",
                            encryption_key=encryption_key,
                            parameter_name="/dc/ynr/dev/1/postgres_host",
                        )
                    ),
                },
                environment={
                    "YNR_DJANGO_SECRET_KEY": "insecure",
                },
            ),
            public_load_balancer=True,
        )
