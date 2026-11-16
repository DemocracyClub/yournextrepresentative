import json

import aws_cdk.assertions as assertions


def _get_web_acl(monkeypatch):
    monkeypatch.setenv("DC_ENVIRONMENT", "development")
    monkeypatch.setenv("CDK_DEFAULT_ACCOUNT", "123")
    monkeypatch.setenv("CDK_DEFAULT_REGION", "eu-west-2")

    # Import here to ensure env is patched
    from app import app

    stack = app.node.find_child("WafStack")
    template = assertions.Template.from_stack(stack)
    web_acls = template.find_resources("AWS::WAFv2::WebACL")
    assert len(web_acls) == 1
    (web_acl,) = web_acls.values()
    return web_acl


def _get_rules(monkeypatch):
    web_acl = _get_web_acl(monkeypatch)
    return {rule["Name"]: rule for rule in web_acl["Properties"]["Rules"]}


def test_existing_rules_unchanged(monkeypatch):
    rules = _get_rules(monkeypatch)
    assert {"RateLimitRule", "AWSCommonRuleSet", "known-bots"} <= set(rules)


def test_require_api_credentials_rule(monkeypatch):
    rules = _get_rules(monkeypatch)
    rule = rules["RequireApiCredentials"]

    assert rule["Action"] == {
        "Block": {
            "CustomResponse": {
                "ResponseCode": 401,
                "CustomResponseBodyKey": "ApiAuthRequired",
                "ResponseHeaders": [
                    {"Name": "WWW-Authenticate", "Value": "Token"}
                ],
            }
        }
    }

    and_statements = rule["Statement"]["AndStatement"]["Statements"]
    assert len(and_statements) == 2
    path_statement, not_statement = and_statements

    prefixes = {
        s["ByteMatchStatement"]["SearchString"]
        for s in path_statement["OrStatement"]["Statements"]
    }
    assert prefixes == {"/api/next/", "/api/v0.9/"}
    for s in path_statement["OrStatement"]["Statements"]:
        assert s["ByteMatchStatement"]["PositionalConstraint"] == "STARTS_WITH"
        assert s["ByteMatchStatement"]["FieldToMatch"] == {"UriPath": {}}

    allowed = not_statement["NotStatement"]["Statement"]["OrStatement"][
        "Statements"
    ]
    fields = [
        json.dumps(
            next(iter(s.values()))["FieldToMatch"],
            sort_keys=True,
        )
        for s in allowed
    ]
    assert sorted(fields) == sorted(
        [
            json.dumps({"SingleQueryArgument": {"Name": "auth_token"}}),
            json.dumps({"SingleHeader": {"Name": "authorization"}}),
            json.dumps({"SingleHeader": {"Name": "cookie"}}),
        ]
    )

    cookie_match = next(
        s["ByteMatchStatement"] for s in allowed if "ByteMatchStatement" in s
    )
    assert cookie_match["SearchString"] == "sessionid="
    assert cookie_match["PositionalConstraint"] == "CONTAINS"


def test_require_api_credentials_response_body(monkeypatch):
    web_acl = _get_web_acl(monkeypatch)
    body = web_acl["Properties"]["CustomResponseBodies"]["ApiAuthRequired"]
    assert body["ContentType"] == "APPLICATION_JSON"
    assert json.loads(body["Content"]) == {
        "detail": "Authentication credentials were not provided."
    }


def test_api_docs_not_protected(monkeypatch):
    rules = _get_rules(monkeypatch)
    rule_json = json.dumps(rules["RequireApiCredentials"])
    assert "/api/docs" not in rule_json
    assert '"/api/"' not in rule_json
