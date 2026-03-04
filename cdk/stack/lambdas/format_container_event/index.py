import json
import logging
import os

import boto3

SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")
DC_ENVIRONMENT = os.environ.get("DC_ENVIRONMENT")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

"""
lambda_handlder() below gets called for all 'ECS Task State Change' events; see
https://docs.aws.amazon.com/AmazonECS/latest/developerguide/ecs_task_events.html

We perform event filterting in this lambda because pure Python is more expressive
than when using the CDK bindings.
"""


def is_health_related_stop(event):
    detail = event.get("detail", {})
    stopped_reason = detail.get("stoppedReason", "").lower()

    # Health-related reasons
    health_reasons = [
        "task failed container health checks",
        "task failed elb health checks",
        "essential container in task exited",
        "container health check failed",
        "failed elb health checks",
        "failed container health checks",
    ]

    # Deployment-related reasons that we choose to ignore
    deployment_reasons = [
        "ecs deployment",
        "scaling activity initiated",
        "service deployment",
    ]

    if any(reason in stopped_reason for reason in health_reasons):
        logger.info(f"Detected health reason: {stopped_reason}")
        return True

    if any(reason in stopped_reason for reason in deployment_reasons):
        logger.info(f"Detected deployment reason: {stopped_reason}")
        return False

    # If we've not determined the reason so far then we check each container
    # exit code
    containers = detail.get("containers", [])
    for container in containers:
        exit_code = container.get("exitCode")
        if exit_code is not None and exit_code != 0:
            logger.info(f"Detected non-zero exit status: {exit_code}")
            return True  # Non-zero exit code suggests failure
    logger.info(
        f"The stop reason was: {stopped_reason}; not one we recognise. Assuming that it's not health-related. If this is wrong then you can add the reason text to the top of the lambda"
    )
    return False


def lambda_handler(event, context):
    logger.info("Going to parse SNS event json")
    # Parse the SNS message from CloudWatch
    try:
        event_json = event["Records"][0]["Sns"]["Message"]
        sns_message = json.loads(event_json)
    except json.JSONDecodeError:
        logger.info(
            f"Failed to parse JSON. Event message started with: {event_json[0:50]}"
        )
        return {"statusCode": 200}
    except (KeyError, IndexError):
        logger.info(
            f"JSON schema changed? Event message started with: {event_json[0:50]}"
        )
        return {"statusCode": 200}

    logger.info("Parsed SNS json")

    if not is_health_related_stop(sns_message):
        logger.info(
            "Lambda triggered due to reasons other than healthcheck (or status) and thus we do not send an email"
        )
        return {"statusCode": 200}

    logger.info(
        "Lambda was triggered due to healthcheck (or exit status) and thus we will send an email"
    )
    logger.info("First we extract the message details")

    timestamp = sns_message.get("time", "UNKNOWN")
    event_type = sns_message.get("detail-type", "UNKNOWN")
    try:
        containers = sns_message["detail"]["containers"]
        container_info = ", ".join(
            f"{c['name']}:{c['lastStatus']}" for c in containers
        )
    except (KeyError, IndexError):
        container_info = "Unknown"

    stopped_reason = sns_message.get("detail", {}).get(
        "stoppedReason", "Unknown"
    )
    stop_code = sns_message.get("detail", {}).get("stoppedCode", "Unknown")

    logger.info("Details extracted")

    # Format custom message
    custom_message = f"""
Event type: {event_type}
Time: {timestamp}

Container info: {container_info}

Reason: {stopped_reason}
Exit code: {stop_code}


Original JSON below:

{event_json}
    """
    logger.info("Custom message composed. Now sending the message")

    if SNS_TOPIC_ARN is None:
        logger.info(
            "Can't send email; Destination topic not set in environment (SNS_TOPIC_ARN)"
        )
        return {"statusCode": 200}

    # Send custom formatted message
    sns = boto3.client("sns")
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=custom_message,
        Subject=f"YNR Container event on {DC_ENVIRONMENT}",
    )
    logger.info("Message sent. We assume success")

    return {"statusCode": 200}
