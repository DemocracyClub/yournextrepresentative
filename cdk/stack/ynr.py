import os

from aws_cdk import CfnOutput, Duration, Stack, Tags
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_kms as kms
from aws_cdk import aws_route53 as route_53
from aws_cdk import aws_route53_targets as route_53_target
from aws_cdk import aws_ssm as ssm
from constructs import Construct


def tag_for_environment():
    """Return a string representing a stable image tag based on the env var
    DC_ENVIRONMENT, or the value 'latest' if it is not set.

    The file app.py (which imports this module) forces one of a set of
    known values, for when it is set.
    """
    if dc_env := os.environ.get("DC_ENVIRONMENT"):
        return dc_env

    return "latest"


class YnrStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.dc_environment = self.node.get_context("dc-environment")

        default_vpc = ec2.Vpc.from_lookup(self, "YnrVpc", is_default=True)
        cluster = ecs.Cluster(self, "YnrCluster", vpc=default_vpc)

        encryption_key = kms.Alias.from_alias_name(
            self, "SSMKey", "alias/aws/ssm"
        )
        image_ref = (
            f"public.ecr.aws/h3q9h5r7/dc-test/ynr:{tag_for_environment()}"
        )

        FQDN = ssm.StringParameter.from_string_parameter_name(
            self,
            "FQDN",
            "FQDN",
        )

        # Secrets aren't necessarily "secret", but are created as
        # environment variables that are looked up at ECS task
        # instantiation.
        common_secrets = {
            "DJANGO_SETTINGS_MODULE": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "DSM",
                    "DJANGO_SETTINGS_MODULE",
                )
            ),
            "YNR_AWS_S3_MEDIA_BUCKET": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "MediaBucketName",
                    "YNR_AWS_S3_MEDIA_BUCKET",
                )
            ),
            "YNR_AWS_S3_MEDIA_REGION": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "MediaBucketRegion",
                    "YNR_AWS_S3_MEDIA_REGION",
                )
            ),
            "YNR_AWS_S3_SOPN_BUCKET": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "SopnBucketName",
                    "YNR_AWS_S3_SOPN_BUCKET",
                )
            ),
            "YNR_AWS_S3_SOPN_REGION": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "SopnBucketRegion",
                    "YNR_AWS_S3_SOPN_REGION",
                )
            ),
            "FQDN": ecs.Secret.from_ssm_parameter(FQDN),
            "POSTGRES_USERNAME": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_secure_string_parameter_attributes(
                    self,
                    "DBUSER",
                    encryption_key=encryption_key,
                    parameter_name="postgres_username",
                )
            ),
            "POSTGRES_PASSWORD": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_secure_string_parameter_attributes(
                    self,
                    "DBPASSWD",
                    encryption_key=encryption_key,
                    parameter_name="postgres_password",
                )
            ),
            "POSTGRES_HOST": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_secure_string_parameter_attributes(
                    self,
                    "DBHOST",
                    encryption_key=encryption_key,
                    parameter_name="postgres_host",
                )
            ),
        }
        common_env_vars = {
            "YNR_DJANGO_SECRET_KEY": "insecure",
        }

        # `alb_basic_auth_token` prevents anyone from accessing the ALB without
        # passing this header. We use it to limit hosts to valid hostnames
        # and to ensure no one can access the ALB directly.

        self.alb_basic_auth_token = (
            ssm.StringParameter.value_for_string_parameter(
                self, "alb_basic_auth_token"
            )
        )

        queue_task_definition = ecs.FargateTaskDefinition(self, "QueueTaskDef")
        queue_task_definition.add_container(
            "queue",
            image=ecs.ContainerImage.from_registry(image_ref),
            secrets=common_secrets,
            memory_limit_mib=512,
            environment=common_env_vars,
            entry_point=["python", "manage.py", "qcluster"],
        )

        queue_service = ecs.FargateService(
            self,
            "QueueService",
            cluster=cluster,
            task_definition=queue_task_definition,
            assign_public_ip=True,
            desired_count=1,
            enable_execute_command=True,
            min_healthy_percent=100,
            capacity_provider_strategies=[
                ecs.CapacityProviderStrategy(
                    capacity_provider="FARGATE", weight=1
                )
            ],
        )

        web_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "YnrService",
            cluster=cluster,
            assign_public_ip=True,
            cpu=512,
            memory_limit_mib=1024,
            desired_count=2,
            enable_execute_command=True,
            task_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC,
            ),
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry(image_ref),
                secrets=common_secrets,
                environment=common_env_vars,
            ),
            public_load_balancer=True,
        )

        # If the X-ALB-Auth is set and valid, forward the request
        web_service.listener.add_action(
            "AllowCloudFrontOnly",
            priority=1,
            conditions=[
                elbv2.ListenerCondition.http_header(
                    name="X-ALB-Auth",
                    values=[self.alb_basic_auth_token],  # exact match
                ),
            ],
            action=elbv2.ListenerAction.forward([web_service.target_group]),
        )

        # if the X-ALB-Auth isn't set or is invalid, raise a 403.
        web_service.listener.add_action(
            "DenyAllOthers",
            priority=2,
            conditions=[elbv2.ListenerCondition.path_patterns(["*"])],
            action=elbv2.ListenerAction.fixed_response(
                status_code=403,
                content_type="text/plain",
                message_body="Forbidden",
            ),
        )

        Tags.of(cluster).add("app", "ynr")
        Tags.of(web_service).add("role", "web")
        Tags.of(queue_service).add("role", "queue")

        # Create CloudFront and related DNS records
        self.create_cloudfront(web_service)

        # Add the FQDN to the CDK output
        CfnOutput(
            self,
            "AppFQDN",
            value=FQDN.string_value,
            description="The FQDN for the CloudFront distribution",
        )

    def create_cloudfront(
        self, service: ecs_patterns.ApplicationLoadBalancedFargateService
    ):
        # Hard code the ARN due to a bug with CDK that means we can't run synth
        # with the placeholder values the SSM interface produces :(
        cert_arns = {
            "development": "arn:aws:acm:us-east-1:539247459606:certificate/e7949af6-5abd-425d-af45-43d86058542f",
            "staging": "arn:aws:acm:us-east-1:523256396133:certificate/9f2cb412-cc62-424b-8d8d-392a6844d564",
            "production": "arn:aws:acm:us-east-1:399683337428:certificate/85e51cc3-acd9-4ae7-b27f-28161df07ef9",
        }
        cert = acm.Certificate.from_certificate_arn(
            self,
            "CertArn",
            certificate_arn=cert_arns.get(self.dc_environment),
        )

        fqdn = ssm.StringParameter.value_from_lookup(
            self,
            "FQDN",
        )

        app_origin = origins.LoadBalancerV2Origin(
            service.load_balancer,
            http_port=80,
            protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
            custom_headers={
                "X-Forwarded-Host": fqdn,
                "X-Forwarded-Proto": "https",
                "X-ALB-Auth": self.alb_basic_auth_token,
            },
        )

        cloudfront_dist = cloudfront.Distribution(
            self,
            "YNRCloudFront",
            default_behavior=cloudfront.BehaviorOptions(
                origin=app_origin,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                compress=True,
            ),
            certificate=cert,
            domain_names=[fqdn],
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,
        )

        # Standard cache policy that allows CSRF headers and
        # doesn't do much else. Caps cache at 5 minutes, to ensure
        # we don't end up caching things for too long.
        short_ttl_forward_headers = cloudfront.CachePolicy(
            self,
            "short_ttl_forward_headers",
            default_ttl=Duration.minutes(0),
            min_ttl=Duration.minutes(0),
            max_ttl=Duration.minutes(5),
            enable_accept_encoding_brotli=True,
            enable_accept_encoding_gzip=True,
            cookie_behavior=cloudfront.CacheCookieBehavior.all(),
            query_string_behavior=cloudfront.CacheQueryStringBehavior.all(),
            header_behavior=cloudfront.CacheHeaderBehavior.allow_list(
                "x-csrfmiddlewaretoken",
                "X-CSRFToken",
                "Accept",
                "Authorization",
                "Cache-Control",
                "Referer",
                "Origin",
            ),
        )

        # Short cache ideal for API endpoints and CSV builder that
        # we want to cahce to prevent hammering, but not for longs
        short_cache = cloudfront.CachePolicy(
            self,
            "short_cache",
            default_ttl=Duration.minutes(2),
            min_ttl=Duration.minutes(0),
            max_ttl=Duration.minutes(10),
            enable_accept_encoding_brotli=True,
            enable_accept_encoding_gzip=True,
            cookie_behavior=cloudfront.CacheCookieBehavior.all(),
            query_string_behavior=cloudfront.CacheQueryStringBehavior.all(),
            header_behavior=cloudfront.CacheHeaderBehavior.allow_list(
                "x-csrfmiddlewaretoken",
                "X-CSRFToken",
                "Accept",
                "Authorization",
                "Cache-Control",
                "Referer",
                "Origin",
            ),
        )

        # Behaviours for different paths
        cloudfront_dist.add_behavior(
            "/admin/*",
            app_origin,
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
            cache_policy=short_ttl_forward_headers,
            compress=True,
        )

        cloudfront_dist.add_behavior(
            "/static/*",
            app_origin,
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
            cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            compress=True,
        )

        cloudfront_dist.add_behavior(
            "/data/export_csv/*",
            app_origin,
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
            cache_policy=short_cache,
            # Enable CORS for CSV downloads
            response_headers_policy=cloudfront.ResponseHeadersPolicy.CORS_ALLOW_ALL_ORIGINS_WITH_PREFLIGHT_AND_SECURITY_HEADERS,
            compress=True,
        )

        hosted_zone = route_53.HostedZone.from_lookup(
            self, "YNRDomain", domain_name=fqdn, private_zone=False
        )
        route_53.ARecord(
            self,
            "FQDN_A_RECORD_TO_CF",
            zone=hosted_zone,
            target=route_53.RecordTarget.from_alias(
                route_53_target.CloudFrontTarget(cloudfront_dist)
            ),
        )
