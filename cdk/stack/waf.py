from aws_cdk import (
    CfnOutput,
    Stack,
)
from aws_cdk import aws_wafv2 as wafv2
from constructs import Construct


class WafStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        web_acl = wafv2.CfnWebACL(
            self,
            "SimpleBotProtectionWAF",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            scope="CLOUDFRONT",
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="SimpleBotProtectionWAF",
                sampled_requests_enabled=True,
            ),
            rules=[
                # 1️⃣ Rate limiting rule: 1000 requests per 5 min per IP
                wafv2.CfnWebACL.RuleProperty(
                    name="RateLimitRule",
                    priority=1,
                    action=wafv2.CfnWebACL.RuleActionProperty(block={}),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        rate_based_statement=wafv2.CfnWebACL.RateBasedStatementProperty(
                            limit=500,
                            aggregate_key_type="IP",
                        )
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="RateLimitRule",
                        sampled_requests_enabled=True,
                    ),
                ),
                wafv2.CfnWebACL.RuleProperty(
                    name="AWSCommonRuleSet",
                    priority=100,
                    override_action=wafv2.CfnWebACL.OverrideActionProperty(
                        none={}
                    ),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                            vendor_name="AWS",
                            name="AWSManagedRulesCommonRuleSet",
                            excluded_rules=[
                                wafv2.CfnWebACL.ExcludedRuleProperty(
                                    name="SizeRestrictions_BODY"
                                ),
                            ],
                        )
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="AWSCommonRuleSet",
                        sampled_requests_enabled=True,
                    ),
                ),
            ],
        )

        CfnOutput(
            self,
            "WebAclArn",
            value=web_acl.attr_arn,
            export_name="YnrWebAclArn",
        )
