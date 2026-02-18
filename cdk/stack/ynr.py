import os

from aws_cdk import CfnOutput, Duration, Stack, Tags
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_cloudwatch_actions as cloudwatch_actions
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as events_targets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from aws_cdk import aws_route53 as route_53
from aws_cdk import aws_route53_targets as route_53_target
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_sns as sns
from aws_cdk import aws_ssm as ssm
from constructs import Construct

ENVIRONMENTS_TO_MONITOR = ["production", "development"]


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
        if self.dc_environment in ENVIRONMENTS_TO_MONITOR:
            monitor_this_env = True
        else:
            monitor_this_env = False

        default_vpc = ec2.Vpc.from_lookup(self, "YnrVpc", is_default=True)
        cluster = ecs.Cluster(
            self,
            "YnrCluster",
            vpc=default_vpc,
            container_insights_v2=ecs.ContainerInsights.ENABLED
            if monitor_this_env
            else ecs.ContainerInsights.DISABLED,
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
        self.common_secrets = {
            "DJANGO_SETTINGS_MODULE": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "DJANGO_SETTINGS_MODULE",
                    "DJANGO_SETTINGS_MODULE",
                )
            ),
            "DJANGO_SECRET_KEY": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "DJANGO_SECRET_KEY",
                    "DJANGO_SECRET_KEY",
                )
            ),
            "DC_ENVIRONMENT": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "DC_ENVIRONMENT",
                    "DC_ENVIRONMENT",
                )
            ),
            "S3_MEDIA_BUCKET": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "S3_MEDIA_BUCKET",
                    "S3_MEDIA_BUCKET",
                )
            ),
            "S3_MEDIA_REGION": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "S3_MEDIA_REGION",
                    "S3_MEDIA_REGION",
                )
            ),
            "S3_SOPN_BUCKET": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "S3_SOPN_BUCKET",
                    "S3_SOPN_BUCKET",
                )
            ),
            "S3_SOPN_REGION": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "S3_SOPN_REGION",
                    "S3_SOPN_REGION",
                )
            ),
            "FQDN": ecs.Secret.from_ssm_parameter(FQDN),
            "SENTRY_DSN": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "SENTRY_DSN",
                    "SENTRY_DSN",
                )
            ),
            "MASTODON_APP_ONLY_BEARER_TOKEN": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "MASTODON_APP_ONLY_BEARER_TOKEN",
                    "MASTODON_APP_ONLY_BEARER_TOKEN",
                )
            ),
            "OPEN_AI_API_KEY": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "OPEN_AI_API_KEY",
                    "OPEN_AI_API_KEY",
                )
            ),
            "SOPN_UPDATE_NOTIFICATION_EMAILS": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "SOPN_UPDATE_NOTIFICATION_EMAILS",
                    "SOPN_UPDATE_NOTIFICATION_EMAILS",
                )
            ),
            "HCAPTCHA_SITEKEY": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "HCAPTCHA_SITEKEY",
                    "HCAPTCHA_SITEKEY",
                )
            ),
            "HCAPTCHA_SECRET": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "HCAPTCHA_SECRET",
                    "HCAPTCHA_SECRET",
                )
            ),
            "ENABLE_SCHEDULED_JOBS": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "ENABLE_SCHEDULED_JOBS",
                    "ENABLE_SCHEDULED_JOBS",
                )
            ),
            "POSTGRES_DBNAME": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "POSTGRES_DBNAME",
                    "POSTGRES_DBNAME",
                )
            ),
            "POSTGRES_USERNAME": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "POSTGRES_USERNAME",
                    "POSTGRES_USERNAME",
                )
            ),
            "POSTGRES_PASSWORD": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "POSTGRES_PASSWORD",
                    "POSTGRES_PASSWORD",
                )
            ),
            "POSTGRES_HOST": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "POSTGRES_HOST",
                    "POSTGRES_HOST",
                )
            ),
            "EMAIL_HOST": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "EMAIL_HOST",
                    "EMAIL_HOST",
                )
            ),
            "EMAIL_HOST_USER": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "EMAIL_HOST_USER",
                    "EMAIL_HOST_USER",
                )
            ),
            "EMAIL_HOST_PASSWORD": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "EMAIL_HOST_PASSWORD",
                    "EMAIL_HOST_PASSWORD",
                )
            ),
            "DEFAULT_FROM_EMAIL": ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "DEFAULT_FROM_EMAIL",
                    "DEFAULT_FROM_EMAIL",
                )
            ),
        }
        if self.dc_environment == "production":
            self.common_secrets["SLACK_TOKEN"] = ecs.Secret.from_ssm_parameter(
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "SLACK_TOKEN",
                    "SLACK_TOKEN",
                )
            )

        # `alb_basic_auth_token` prevents anyone from accessing the ALB without
        # passing this header. We use it to limit hosts to valid hostnames
        # and to ensure no one can access the ALB directly.

        self.alb_basic_auth_token = (
            ssm.StringParameter.value_for_string_parameter(
                self, "alb_basic_auth_token"
            )
        )

        worker_task_definition = ecs.FargateTaskDefinition(
            self,
            "WorkerTaskDef",
            cpu=1024,
            memory_limit_mib=2048,
        )

        # Add X-Ray daemon sidecar for worker
        worker_task_definition.add_container(
            "xray-daemon-worker",
            image=ecs.ContainerImage.from_registry(
                "public.ecr.aws/xray/aws-xray-daemon:latest"
            ),
            cpu=32,
            memory_limit_mib=256,
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="YnrXRayWorker",
                log_retention=logs.RetentionDays.THREE_MONTHS,
            ),
        )

        worker_task_definition.add_container(
            "worker",
            image=ecs.ContainerImage.from_registry(image_ref),
            secrets=self.common_secrets,
            entry_point=["python", "manage.py", "qcluster"],
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="YnrService",
                log_retention=logs.RetentionDays.THREE_MONTHS,
            ),
        )

        worker_service = ecs.FargateService(
            self,
            "WorkerService",
            cluster=cluster,
            task_definition=worker_task_definition,
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

        web_desired_count = 1
        if self.dc_environment == "production":
            web_desired_count = 2

        web_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "YnrService",
            cluster=cluster,
            assign_public_ip=True,
            cpu=1024,
            memory_limit_mib=2048,
            desired_count=web_desired_count,
            circuit_breaker={"rollback": True},
            enable_execute_command=True,
            task_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC,
            ),
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry(image_ref),
                secrets=self.common_secrets,
                log_driver=ecs.LogDrivers.aws_logs(
                    stream_prefix="YnrService",
                    log_retention=logs.RetentionDays.THREE_MONTHS,
                ),
            ),
            public_load_balancer=True,
        )

        # Add X-Ray daemon sidecar to web service
        web_service.task_definition.add_container(
            "xray-daemon-web",
            image=ecs.ContainerImage.from_registry(
                "public.ecr.aws/xray/aws-xray-daemon:latest"
            ),
            cpu=32,
            memory_limit_mib=256,
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="YnrXRayWeb",
                log_retention=logs.RetentionDays.THREE_MONTHS,
            ),
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

        web_service.target_group.configure_health_check(
            path="/status_check/",
            healthy_http_codes="200",
        )

        # See https://github.com/aws/aws-cdk/issues/31529
        # When that issue is addressed we will be able to configure the web_service/target_group directly
        web_service.target_group.set_attribute(
            "deregistration_delay.timeout_seconds", "60"
        )

        Tags.of(cluster).add("app", "ynr")
        Tags.of(web_service).add("role", "web")
        Tags.of(worker_service).add("role", "worker")

        s3_resources = ["arn:aws:s3:::ynr-*"]
        if self.dc_environment == "production":
            s3_resources = [
                "arn:aws:s3:::ynr-*",
                "arn:aws:s3:::public-sopns",
                "arn:aws:s3:::public-sopns/*",
                "arn:aws:s3:::static-candidates.democracyclub.org.uk",
                "arn:aws:s3:::static-candidates.democracyclub.org.uk/*",
            ]

        s3_policy_statement = iam.PolicyStatement(
            actions=["s3:*"],
            resources=s3_resources,
            effect=iam.Effect.ALLOW,
        )
        worker_service.task_definition.task_role.add_to_policy(
            s3_policy_statement
        )
        web_service.task_definition.task_role.add_to_policy(s3_policy_statement)

        worker_service.task_definition.task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonRekognitionFullAccess"
            )
        )
        worker_service.task_definition.task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonTextractFullAccess"
            )
        )
        web_service.task_definition.task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonRekognitionFullAccess"
            )
        )
        web_service.task_definition.task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonTextractFullAccess"
            )
        )

        # Add X-Ray permissions for both web and worker services
        xray_policy_statement = iam.PolicyStatement(
            actions=[
                "xray:PutTraceSegments",
                "xray:PutTelemetryRecords",
                "xray:GetSamplingRules",
                "xray:GetSamplingTargets",
                "xray:GetSamplingStatisticSummaries",
            ],
            resources=["*"],
            effect=iam.Effect.ALLOW,
        )
        worker_service.task_definition.task_role.add_to_policy(
            xray_policy_statement
        )
        web_service.task_definition.task_role.add_to_policy(
            xray_policy_statement
        )

        # Create CloudFront and related DNS records
        self.create_cloudfront(web_service)

        # Add the FQDN to the CDK output
        CfnOutput(
            self,
            "AppFQDN",
            value=FQDN.string_value,
            description="The FQDN for the CloudFront distribution",
        )
        CfnOutput(
            self,
            "CloudFrontDistributionId",
            value=self.cloudfront_dist.distribution_id,
            export_name="YnrCloudFrontDistributionId",
        )

        # Alerting / notification
        if monitor_this_env:
            alert_email_recipient = (
                ssm.StringParameter.from_string_parameter_name(
                    self,
                    "alert_email_recipient",
                    "alert_email_recipient",
                )
            )
            metric_topic = sns.Topic(
                self,
                "metricalert",
                display_name="container metric alert",
            )

            container_topic = sns.Topic(
                self, "containerevent", display_name="container event alert"
            )

            # The symbolic names we give the alerts need to be unique, so we simply append a digit based on the service being monitored
            for service_info in [
                {"name": web_service.service.service_name, "id": 0},
                {"name": worker_service.service_name, "id": 1},
            ]:
                cpu_alarm = cloudwatch.Alarm(
                    self,
                    f"ECSCpuUtilizationAlarm{service_info['id']}",
                    alarm_name=f"{service_info['name']}-cpu-high",
                    alarm_description=f"CPU utilization is high for ECS service {service_info['name']}",
                    metric=cloudwatch.Metric(
                        namespace="AWS/ECS",
                        metric_name="CPUUtilization",
                        dimensions_map={
                            "ServiceName": service_info["name"],
                            "ClusterName": cluster.cluster_name,
                        },
                        statistic="Average",
                        period=Duration.seconds(60),
                    ),
                    threshold=80.0,  # This is a percentage
                    comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                    evaluation_periods=3,
                    datapoints_to_alarm=2,
                    treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
                )
                cpu_alarm.add_alarm_action(
                    cloudwatch_actions.SnsAction(metric_topic)
                )

                cpu_alarm.add_ok_action(
                    cloudwatch_actions.SnsAction(metric_topic)
                )

                memory_alarm = cloudwatch.Alarm(
                    self,
                    f"ECSMemoryUtilizationAlarm{service_info['id']}",
                    alarm_name=f"{service_info['name']}-memory-high",
                    alarm_description=f"High memory utilization detected for ECS service {service_info['name']}",
                    metric=cloudwatch.Metric(
                        namespace="AWS/ECS",
                        metric_name="MemoryUtilization",
                        dimensions_map={
                            "ServiceName": service_info["name"],
                            "ClusterName": cluster.cluster_name,
                        },
                        statistic="Average",
                        period=Duration.seconds(60),
                    ),
                    threshold=85.0,  # This is a percentage
                    comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
                    evaluation_periods=3,
                    datapoints_to_alarm=2,
                    treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
                )

                memory_alarm.add_alarm_action(
                    cloudwatch_actions.SnsAction(metric_topic)
                )

                memory_alarm.add_ok_action(
                    cloudwatch_actions.SnsAction(metric_topic)
                )

            sns.Subscription(
                self,
                "MetricSubscription",
                topic=metric_topic,
                endpoint=alert_email_recipient.string_value,
                protocol=sns.SubscriptionProtocol.EMAIL,
            )

            sns.Subscription(
                self,
                "EmailSubscription",
                topic=container_topic,
                endpoint=alert_email_recipient.string_value,
                protocol=sns.SubscriptionProtocol.EMAIL,
            )
            default_bus = events.EventBus.from_event_bus_name(
                self, "EventBus", "default"
            )
            container_events_rule = events.Rule(
                self,
                "email-notify",
                rule_name="email-notify",
                description="YNR Task failure",
                event_bus=default_bus,
                event_pattern=events.EventPattern(
                    source=["aws.ecs"],
                    detail={"clusterArn": [cluster.cluster_arn]},
                    detail_type=[
                        "ECS Task State Change",
                        "ECS Container Instance State Change",
                    ],
                ),
            )
            container_events_rule.add_target(
                events_targets.SnsTopic(container_topic)
            )

            filtered_rule = events.Rule(
                self,
                "FilteredECSAlertsRule",
                rule_name="filtered-alerts-rule",
                description="YNR Task/Container alerts",
                event_pattern=events.EventPattern(
                    source=["aws.ecs"],
                    detail_type=["ECS Task State Change"],
                    detail={
                        "clusterArn": [cluster.cluster_arn],
                        "launchType": ["FARGATE"],
                        "lastStatus": ["STOPPED"],
                        "stopCode": [
                            {
                                "anything-but": [
                                    "ServiceSchedulerInitiated",  # Normal deployments
                                    "UserInitiated",  # Manual stops by an AWS Console user
                                ]
                            }
                        ],
                    },
                ),
            )

            filtered_rule.add_target(events_targets.SnsTopic(container_topic))

    def create_cloudfront(
        self, service: ecs_patterns.ApplicationLoadBalancedFargateService
    ):
        # Hard code the ARN due to a bug with CDK that means we can't run synth
        # with the placeholder values the SSM interface produces :(
        cert_arns = {
            "development": "arn:aws:acm:us-east-1:539247459606:certificate/e7949af6-5abd-425d-af45-43d86058542f",
            "staging": "arn:aws:acm:us-east-1:523256396133:certificate/9f2cb412-cc62-424b-8d8d-392a6844d564",
            "production": "arn:aws:acm:us-east-1:399683337428:certificate/d0f8d2a5-d0ab-41b7-a0ed-76073317c57c",
            "training": "arn:aws:acm:us-east-1:797583072753:certificate/c3d50397-8879-4c4e-a433-85a45c98c3d4",
        }
        cert = acm.Certificate.from_certificate_arn(
            self,
            "CertArn",
            certificate_arn=cert_arns.get(self.dc_environment),
        )

        web_acl_arn = self.node.try_get_context("webAclArn")

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

        S3_MEDIA_BUCKET = ssm.StringParameter.from_string_parameter_name(
            self,
            "S3_MEDIA_BUCKET_PARAM",
            "S3_MEDIA_BUCKET",
        )

        s3_media_origin = origins.S3BucketOrigin(
            bucket=s3.Bucket.from_bucket_name(
                self,
                "ynr-media-bucket",
                bucket_name=S3_MEDIA_BUCKET.string_value,
            ),
        )

        self.cloudfront_dist = cloudfront.Distribution(
            self,
            "YNRCloudFront",
            web_acl_id=web_acl_arn,
            default_behavior=cloudfront.BehaviorOptions(
                origin=app_origin,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cache_policy=cloudfront.CachePolicy(
                    self,
                    "short_cache_not_authenticated_id",
                    default_ttl=Duration.minutes(10),
                    min_ttl=Duration.minutes(0),
                    max_ttl=Duration.minutes(120),
                    enable_accept_encoding_brotli=True,
                    enable_accept_encoding_gzip=True,
                    cookie_behavior=cloudfront.CacheCookieBehavior.all(),
                    query_string_behavior=cloudfront.CacheQueryStringBehavior.all(),
                    header_behavior=cloudfront.CacheHeaderBehavior.allow_list(
                        "x-csrfmiddlewaretoken",
                        "X-CSRFToken",
                        "Accept",
                        "Accept-Language",
                        "Authorization",
                        "Cache-Control",
                        "Referer",
                    ),
                ),
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
        self.cloudfront_dist.add_behavior(
            "/admin/*",
            app_origin,
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
            cache_policy=short_ttl_forward_headers,
            compress=True,
        )

        self.cloudfront_dist.add_behavior(
            "/static/*",
            app_origin,
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
            cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            compress=True,
        )
        self.cloudfront_dist.add_behavior(
            "/media/*",
            s3_media_origin,
            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
            cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            compress=True,
        )

        self.cloudfront_dist.add_behavior(
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
                route_53_target.CloudFrontTarget(self.cloudfront_dist)
            ),
        )
