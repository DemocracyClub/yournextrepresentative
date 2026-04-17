from aws_cdk import (
    CfnOutput,
    Stack,
)
from aws_cdk import aws_wafv2 as wafv2
from constructs import Construct

KNOWN_BOT_PATTERNS = [
    "pcore-http/v0.24.5",
    "semrushbot",
    "megaindex.ru",
    "mj12bot",
    "ahrefsbot",
    "sogou",
    "mauibot",
    "gofeed",
    "msnbot",
    "aspiegelbot",
    "yandex",
    "goodbot",
    "seekport",
    "barkrowler",
    "screaming frog",
    "petalbot",
    "dataforsebot",
    "codemantra",
    "scrapy",
    "dotbot",
    "homeassistant",
    "seokicks",
    "okhttp",
    "blexbot",
    "turnitin",
    "anthropic-ai",
    "bytespider",
    "go-http-client",
    "gptbot",
    "fidget-spinner-bot",
    "thesis-research-bot",
    "backgroundshortcutrunner",
    "amazonbot",
    "claudebot",
    "happywing",
    "googleother",
    "aiohttp",
    "imagesiftbot",
    "oai-searchbot",
    "friendlycrawler",
    "timpibot",
    "awariobot",
    "meta-externalagent",
    "serpstatbot",
    "yisoupspider",
    "google-cloudvertexbot",
    "lanai",
    "baiduspider",
    "webscanner",
    "perplexity",
    "findfiles.net",
    "headlesschrome",
    "amazon-quick",
    "sleepbot",
    "seamus the search engine",
]


class WafStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        known_bots_pattern_set = wafv2.CfnRegexPatternSet(
            self,
            "KnownBotsPatternSet",
            name="KnownBotsPatternSet",
            scope="CLOUDFRONT",
            regular_expression_list=KNOWN_BOT_PATTERNS,
        )

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
                # Rate limiting rule: 500 requests per 5 min per IP
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
                        count={}
                    ),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                            vendor_name="AWS",
                            name="AWSManagedRulesCommonRuleSet",
                            rule_action_overrides=[
                                wafv2.CfnWebACL.RuleActionOverrideProperty(
                                    name="SizeRestrictions_BODY",
                                    action_to_use=wafv2.CfnWebACL.RuleActionProperty(
                                        count={}
                                    ),
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
                # Block known bots and scrapers by user-agent (returns 418)
                wafv2.CfnWebACL.RuleProperty(
                    name="known-bots",
                    priority=101,
                    action=wafv2.CfnWebACL.RuleActionProperty(
                        block=wafv2.CfnWebACL.BlockActionProperty(
                            custom_response=wafv2.CfnWebACL.CustomResponseProperty(
                                response_code=418,
                            )
                        )
                    ),
                    statement=wafv2.CfnWebACL.StatementProperty(
                        regex_pattern_set_reference_statement=wafv2.CfnWebACL.RegexPatternSetReferenceStatementProperty(
                            arn=known_bots_pattern_set.attr_arn,
                            field_to_match=wafv2.CfnWebACL.FieldToMatchProperty(
                                single_header={"Name": "user-agent"},
                            ),
                            text_transformations=[
                                wafv2.CfnWebACL.TextTransformationProperty(
                                    priority=0,
                                    type="LOWERCASE",
                                )
                            ],
                        )
                    ),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        cloud_watch_metrics_enabled=True,
                        metric_name="known-bots",
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
